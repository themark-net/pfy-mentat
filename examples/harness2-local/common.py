#!/usr/bin/env python3
"""Pins, paths, dotenv checks, and the real-HOME fingerprint for harness2-local.

The fingerprint imports ``home_sig`` from examples/x-intake-local/smoke_128_130.py.
On this host ``~/.cache/uv`` is about 21 GiB and ``~/.npm`` about 3.6 GiB, so a
content hash of every watched tree on every stage step does not fit the session
cap (decision D1). Trees at most 32 MiB are mixed with the real ``home_sig``
digest. Larger trees use the same entry fields ``home_sig`` records (path, type,
mode, mtime_ns, size, inode, symlink target) without reading file bodies. A
created, deleted, resized, or retouched entry still changes the digest.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

H2_PIN = "1cfe254e8d25b15f37048c3730134686abe60335"
OC_PIN = "23fb5e0516c99ac04a1aa46c193efda2e1b9bb24"
OC_VERSION = "1.14.18"
SOLVER_MODEL = "llamacpp/qwen3.6-35b"
IMPROVER_MODEL = "llamacpp/qwen3.6-35b"
RELAY_PORT_DEFAULT = 8766
CONTENT_CAP = 32 * 1024 * 1024

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

HOME_WATCH = (
    ".cache/uv",
    ".local/share/uv",
    ".npm",
    ".bun",
    ".config/opencode",
    ".local/share/opencode",
    ".cache/opencode",
    ".local/state/opencode",
)

REQUIRED_ENV = (
    "HARNESS2_SOLVER_MODEL",
    "HARNESS2_IMPROVER_MODEL",
    "HARNESS2_RUNS_DIR",
)

OPENCODE_DISABLE = (
    "OPENCODE_DISABLE_MODELS_FETCH",
    "OPENCODE_DISABLE_AUTOUPDATE",
    "OPENCODE_DISABLE_LSP_DOWNLOAD",
    "OPENCODE_DISABLE_DEFAULT_PLUGINS",
    "OPENCODE_DISABLE_EXTERNAL_SKILLS",
    "OPENCODE_DISABLE_CLAUDE_CODE",
)


def worktree() -> Path:
    env = os.environ.get("HARNESS2_W")
    if env:
        return Path(env).resolve()
    return REPO


def state_dir() -> Path:
    return worktree() / "tmp" / "state"


def harness_root() -> Path:
    return worktree() / "tmp" / "harness2"


def parse_dotenv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def check_dotenv(env: dict[str, str]) -> str | None:
    """Return the first local-only .env error, or None.

    A missing required name is reported as ``missing <NAME>``. A Vertex model
    or a ``GOOGLE_*`` / ``*VERTEX*`` name is ``Vertex is not allowed``.
    """
    for key in REQUIRED_ENV:
        if not str(env.get(key, "")).strip():
            return f"missing {key}"
    for key in env:
        upper = key.upper()
        if upper.startswith("GOOGLE_") or "VERTEX" in upper:
            return "Vertex is not allowed"
        if "JUDGE" in upper:
            return f"judge var not allowed: {key}"
    for key in ("HARNESS2_SOLVER_MODEL", "HARNESS2_IMPROVER_MODEL"):
        if "vertex" in str(env.get(key, "")).lower():
            return "Vertex is not allowed"
    return None


def _home_sig():
    xdir = REPO / "examples" / "x-intake-local"
    if str(xdir) not in sys.path:
        sys.path.insert(0, str(xdir))
    import smoke_128_130  # noqa: E402

    return smoke_128_130.home_sig


def _present(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _meta(path: Path) -> tuple[str, int] | None:
    """Structural digest and total regular-file bytes. Nested symlinks are not followed."""
    if not _present(path):
        return None
    hasher = hashlib.sha256()
    total = 0

    def walk(node: Path) -> None:
        nonlocal total
        try:
            st = node.lstat()
        except OSError as exc:
            hasher.update(f"{node}:err:{exc.errno}\n".encode())
            return
        mode = stat.S_IMODE(st.st_mode)
        kind = stat.S_IFMT(st.st_mode)
        if stat.S_ISLNK(st.st_mode):
            try:
                target = os.readlink(node)
            except OSError as exc:
                target = f"err:{exc.errno}"
            hasher.update(f"{node}:link:{kind:o}:{mode:o}:{st.st_mtime_ns}:{target}\n".encode())
            return
        if stat.S_ISDIR(st.st_mode):
            hasher.update(f"{node}:dir:{kind:o}:{mode:o}:{st.st_mtime_ns}\n".encode())
            try:
                names = sorted(os.listdir(node))
            except OSError as exc:
                hasher.update(f"{node}:unlistable:{exc.errno}\n".encode())
                return
            for name in names:
                walk(node / name)
            return
        total += int(st.st_size)
        hasher.update(
            f"{node}:file:{kind:o}:{mode:o}:{st.st_mtime_ns}:{st.st_size}:{st.st_ino}\n".encode()
        )

    root = path
    try:
        st = path.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(st.st_mode):
        walk(path)
        try:
            root = Path(os.path.realpath(path))
        except OSError:
            root = path
        if root != path and _present(root):
            walk(root)
    else:
        walk(path)
    return hasher.hexdigest(), total


def home_snapshot(home: Path | None = None) -> dict[str, str | None]:
    """Map each watched path (relative to home) to a digest, or None if it is absent."""
    root = home if home is not None else Path.home()
    sig_fn = _home_sig()
    out: dict[str, str | None] = {}
    for rel in HOME_WATCH:
        path = root / rel
        meta = _meta(path)
        if meta is None:
            out[rel] = None
            continue
        digest, total = meta
        if total <= CONTENT_CAP:
            content = sig_fn(path)
            mixed = hashlib.sha256(f"{digest}|home_sig|{content}".encode()).hexdigest()
            out[rel] = mixed
        else:
            out[rel] = hashlib.sha256(f"{digest}|lstat-only".encode()).hexdigest()
    return out


def format_snapshot(snap: dict[str, str | None]) -> str:
    lines = []
    for rel in HOME_WATCH:
        sig = snap.get(rel)
        lines.append(f"{rel}\t{'-' if sig is None else sig}")
    return "\n".join(lines) + "\n"


def parse_snapshot(text: str) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for line in text.splitlines():
        if "\t" not in line:
            continue
        rel, sig = line.split("\t", 1)
        out[rel] = None if sig == "-" else sig
    return out


def snapshot_diff(before: dict[str, str | None], after: dict[str, str | None]) -> list[str]:
    changed = []
    for rel in HOME_WATCH:
        if before.get(rel) != after.get(rel):
            changed.append(rel)
    return changed


def scrub_env(env: dict[str, str]) -> dict[str, str]:
    """Drop paid-key names, GOOGLE_*/VERTEX*, and token-shaped names."""
    xdir = REPO / "examples" / "x-intake-local"
    if str(xdir) not in sys.path:
        sys.path.insert(0, str(xdir))
    import smoke  # noqa: E402

    out: dict[str, str] = {}
    for key, value in env.items():
        upper = key.upper()
        if key in smoke.PAID_KEYS:
            continue
        if upper.startswith("GOOGLE_") or "VERTEX" in upper:
            continue
        if smoke.SECRET_ENV_RE.search(key):
            continue
        out[key] = value
    return out


def relay_port() -> int:
    """Port shared by the generated OpenCode config and by sbun.

    ``HARNESS2_RELAY_PORT`` is the only source. An unset or non-numeric value
    is unknown: the caller must fail closed instead of hanging with no route.
    """
    raw = os.environ.get("HARNESS2_RELAY_PORT", "").strip()
    if raw.isdigit() and 1 <= int(raw) <= 65535:
        return int(raw)
    raise ValueError("relay port unknown")


def write_opencode_config(port: int | None = None) -> Path:
    """Write $W/tmp/state/opencode.json for the llamacpp provider.

    The shape starts from examples/opencode-ollama/opencode.json.template
    (schema and provider/npm fields). apiKey is the dummy string ``local``.
    """
    if port is None:
        try:
            port = relay_port()
        except ValueError:
            port = RELAY_PORT_DEFAULT
    template_path = REPO / "examples" / "opencode-ollama" / "opencode.json.template"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    model = "qwen3.6-35b"
    cfg = {
        "$schema": template.get("$schema", "https://opencode.ai/config.json"),
        "provider": {
            "llamacpp": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "llama.cpp (local)",
                "options": {
                    "baseURL": f"http://127.0.0.1:{int(port)}/v1",
                    "apiKey": "local",
                },
                "models": {
                    model: {
                        "name": model,
                        "options": {"temperature": 0, "seed": 230},
                    }
                },
            }
        },
        "model": f"llamacpp/{model}",
    }
    dest = state_dir() / "opencode.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return dest


def _cli(argv: list[str]) -> int:
    if len(argv) < 1:
        print(
            "usage: common.py home-snapshot|home-diff|write-opencode-config|relay-port",
            file=sys.stderr,
        )
        return 2
    cmd = argv[0]
    if cmd == "home-snapshot":
        sys.stdout.write(format_snapshot(home_snapshot()))
        return 0
    if cmd == "home-diff":
        if len(argv) != 3:
            print("usage: common.py home-diff BEFORE AFTER", file=sys.stderr)
            return 2
        before = parse_snapshot(Path(argv[1]).read_text(encoding="utf-8"))
        after = parse_snapshot(Path(argv[2]).read_text(encoding="utf-8"))
        changed = snapshot_diff(before, after)
        for rel in changed:
            print(rel)
        return 2 if changed else 0
    if cmd == "write-opencode-config":
        path = write_opencode_config()
        print(path)
        return 0
    if cmd == "relay-port":
        try:
            print(relay_port())
        except ValueError:
            print("BLOCKED: relay port unknown (set HARNESS2_RELAY_PORT)", file=sys.stderr)
            return 2
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
