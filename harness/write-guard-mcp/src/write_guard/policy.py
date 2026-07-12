"""Path policy for write-guard (stdlib + optional PyYAML)."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass
class Policy:
    roots: list[str] = field(default_factory=lambda: ["/workspace"])
    deny_globs: list[str] = field(default_factory=list)
    allow_write_globs: list[str] = field(default_factory=lambda: ["/**"])
    deny_write_globs: list[str] = field(default_factory=list)
    allow_delete_globs: list[str] = field(default_factory=list)
    default_mode: str = "audit"
    audit_log: str = "/workspace/.write-guard-audit.jsonl"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        modes = data.get("modes") or {}
        return cls(
            roots=list(data.get("roots") or ["/workspace"]),
            deny_globs=list(data.get("deny_globs") or []),
            allow_write_globs=list(data.get("allow_write_globs") or ["/**"]),
            deny_write_globs=list(data.get("deny_write_globs") or []),
            allow_delete_globs=list(data.get("allow_delete_globs") or []),
            default_mode=str(modes.get("default") or data.get("default_mode") or "audit"),
            audit_log=str(data.get("audit_log") or "/workspace/.write-guard-audit.jsonl"),
        )


def load_policy(path: str | Path | None = None) -> Policy:
    """Load YAML policy; fall back to built-in defaults."""
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path))
    env = os.environ.get("WRITE_GUARD_POLICY")
    if env:
        candidates.append(Path(env))
    # package-adjacent default
    here = Path(__file__).resolve().parents[2] / "policy.default.yaml"
    candidates.append(here)

    for p in candidates:
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            if yaml is None:
                raise RuntimeError("PyYAML required to load policy file")
            data = yaml.safe_load(text) or {}
            return Policy.from_dict(data)
    return Policy()


def resolve_mode(policy: Policy, env: dict[str, str] | None = None) -> str:
    e = env if env is not None else os.environ
    mode = (e.get("WRITE_GUARD_MODE") or policy.default_mode or "audit").strip().lower()
    if mode not in ("off", "audit", "enforce"):
        mode = "audit"
    return mode


def resolve_roots(policy: Policy, env: dict[str, str] | None = None) -> list[str]:
    e = env if env is not None else os.environ
    raw = e.get("WRITE_GUARD_ROOTS")
    if raw:
        return [r.strip() for r in raw.split(":") if r.strip()]
    return list(policy.roots)


def _norm(path: str) -> str:
    # Prefer posix-style for glob matching inside containers
    p = path.replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p
    # collapse //
    while "//" in p:
        p = p.replace("//", "/")
    return p


def under_roots(path: str, roots: list[str]) -> bool:
    np = _norm(path)
    for r in roots:
        nr = _norm(r).rstrip("/") or "/"
        if np == nr or np.startswith(nr + "/"):
            return True
    return False


def match_globs(path: str, globs: list[str]) -> str | None:
    """Return first matching glob or None. Supports ** via recursive path segments."""
    np = _norm(path)
    name = PurePosixPath(np).name
    for g in globs:
        g = g.replace("\\", "/")
        # fnmatch does not treat ** specially; add common cases
        patterns = [g]
        if g.startswith("**/"):
            patterns.append(g[3:])
            patterns.append("*/" + g[3:])
            patterns.append("*/*/" + g[3:])
            patterns.append(name if g[3:] == name or g.endswith(name) else g)
        if any(fnmatch.fnmatch(np, pat) or fnmatch.fnmatch(name, pat) for pat in patterns):
            return g
        # also match basename-only patterns like **/.env
        if g.endswith(name) or g.endswith("/" + name) or g == name:
            if fnmatch.fnmatch(name, PurePosixPath(g).name):
                return g
        # path contains segment
        if "**/" in g:
            suffix = g.split("**/", 1)[-1]
            if fnmatch.fnmatch(name, suffix) or fnmatch.fnmatch(np, "*/" + suffix) or np.endswith("/" + suffix):
                return g
    return None


@dataclass
class Decision:
    allow: bool
    reason: str
    mode: str
    path: str


def decide(
    path: str,
    *,
    op: str,
    mode: str,
    policy: Policy,
    roots: list[str] | None = None,
) -> Decision:
    """Decide allow/deny for read|write|delete|list."""
    roots = roots if roots is not None else resolve_roots(policy)
    np = _norm(path)
    mode = mode.lower()

    if mode == "off":
        return Decision(True, "mode=off", mode, np)

    if not under_roots(np, roots):
        if mode == "enforce":
            return Decision(False, "outside WRITE_GUARD_ROOTS", mode, np)
        return Decision(True, "outside roots but mode=audit (allowed+logged)", mode, np)

    hit = match_globs(np, policy.deny_globs)
    if hit and op in ("write", "delete", "read"):
        # secrets: block write/delete always in enforce; block write/delete in audit still allow read
        if op in ("write", "delete"):
            if mode == "enforce":
                return Decision(False, f"deny_globs matched {hit!r}", mode, np)
            # audit: still allow but flag reason
            if op == "write":
                return Decision(True, f"audit: would deny deny_globs {hit!r}", mode, np)

    if op == "write":
        dhit = match_globs(np, policy.deny_write_globs)
        if dhit:
            if mode == "enforce":
                return Decision(False, f"deny_write_globs matched {dhit!r}", mode, np)
            return Decision(True, f"audit: would deny deny_write_globs {dhit!r}", mode, np)
        if policy.allow_write_globs:
            ahit = match_globs(np, policy.allow_write_globs)
            if not ahit:
                # allow "/workspace/**" style — if no match, check under roots as implicit allow
                if not under_roots(np, roots):
                    if mode == "enforce":
                        return Decision(False, "not in allow_write_globs", mode, np)
                # if under roots and allow is /** style, match_globs may fail — treat under-roots as allow
                if under_roots(np, roots):
                    return Decision(True, "under roots", mode, np)
                if mode == "enforce":
                    return Decision(False, "not in allow_write_globs", mode, np)
        return Decision(True, "write allowed", mode, np)

    if op == "delete":
        if policy.allow_delete_globs:
            ahit = match_globs(np, policy.allow_delete_globs)
            if not ahit:
                if mode == "enforce":
                    return Decision(False, "delete not in allow_delete_globs", mode, np)
                return Decision(True, "audit: delete would be denied", mode, np)
        else:
            if mode == "enforce":
                return Decision(False, "delete default deny (no allow_delete_globs)", mode, np)
            return Decision(True, "audit: delete default deny skipped", mode, np)

    # read / list
    return Decision(True, "read/list allowed", mode, np)
