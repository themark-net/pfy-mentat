"""Registry loaders for the toolset x harness matrix (ADR-0017).

Reads ``data/harnesses.json`` (harness axis: rows with ``role == "harness"``)
and ``data/toolsets.json`` (toolset axis). ``validate()`` returns a list of
human-readable problems so CLI, tests and ``scripts/catalog_check.py`` share
one definition of "well-formed".
"""
from __future__ import annotations

import json
import os
from pathlib import Path

STATUSES = ("implemented", "partial", "stub")
LANES = ("local", "cloud")
HARNESS_ROLE = "harness"


def root(explicit: str | os.PathLike | None = None) -> Path:
    """Repo root: explicit arg, then ``PFY_ROOT``, then two levels above this file."""
    if explicit:
        return Path(explicit).resolve()
    env = os.environ.get("PFY_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[1]


def state_dir(explicit: str | os.PathLike | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    return Path(os.environ.get("PFY_STATE_DIR") or (Path.home() / ".pfy-mentat")).expanduser()


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("%s: top level is not an object" % path)
    return data


def load_harnesses(root_dir: Path | None = None) -> dict:
    return _load_json(root(root_dir) / "data" / "harnesses.json")


def load_toolsets(root_dir: Path | None = None) -> dict:
    return _load_json(root(root_dir) / "data" / "toolsets.json")


def harness_rows(root_dir: Path | None = None, *, role: str = HARNESS_ROLE) -> list[dict]:
    rows = load_harnesses(root_dir).get("harnesses") or []
    return [h for h in rows if isinstance(h, dict) and h.get("role") == role]


def harness_ids(root_dir: Path | None = None) -> list[str]:
    return [str(h["id"]) for h in harness_rows(root_dir) if h.get("id")]


def harness(hid: str, root_dir: Path | None = None) -> dict | None:
    for h in load_harnesses(root_dir).get("harnesses") or []:
        if isinstance(h, dict) and h.get("id") == hid:
            return h
    return None


ATTACH_KEYS = ("session_id", "label", "issue", "script", "bin_fallbacks", "next_install", "config_dir")


def attach_profile(hid: str, root_dir: Path | None = None) -> dict | None:
    """Per-harness attach differences (T-0121) or None when the harness has no ``attach`` object.

    Returns a flat dict: id, session_id, label, issue, script, binaries (from
    ``detect``), bin_fallbacks, next_install, config_dir_env, config_dir_default.
    """
    h = harness(hid, root_dir)
    if not h or not isinstance(h.get("attach"), dict):
        return None
    a = h["attach"]
    cfg = a.get("config_dir") if isinstance(a.get("config_dir"), dict) else {}
    return {
        "id": str(h.get("id")),
        "session_id": str(a.get("session_id") or h.get("id")),
        "label": str(a.get("label") or h.get("name") or h.get("id")),
        "issue": a.get("issue"),
        "script": str(a.get("script") or ""),
        "binaries": tuple(str(b) for b in (h.get("detect") or [])),
        "bin_fallbacks": tuple(str(b) for b in (a.get("bin_fallbacks") or [])),
        "next_install": a.get("next_install") or None,
        "config_dir_env": str(cfg.get("env") or "") or None,
        "config_dir_default": str(cfg.get("default") or "") or None,
    }


def attach_harness_ids(root_dir: Path | None = None) -> list[str]:
    return [str(h["id"]) for h in harness_rows(root_dir) if h.get("id") and isinstance(h.get("attach"), dict)]


def harness_home(hid: str, root_dir: Path | None = None) -> Path | None:
    """Harness-native writable config dir (env override -> default), or None."""
    prof = attach_profile(hid, root_dir)
    if not prof or not prof["config_dir_env"]:
        return None
    return Path(os.environ.get(prof["config_dir_env"]) or prof["config_dir_default"]).expanduser()


def toolset_rows(root_dir: Path | None = None) -> list[dict]:
    return [t for t in (load_toolsets(root_dir).get("toolsets") or []) if isinstance(t, dict)]


def toolset_ids(root_dir: Path | None = None) -> list[str]:
    return [str(t["id"]) for t in toolset_rows(root_dir) if t.get("id")]


def toolset(tid: str, root_dir: Path | None = None) -> dict | None:
    for t in toolset_rows(root_dir):
        if t.get("id") == tid:
            return t
    return None


def _validate_attach(h: dict) -> list[str]:
    hid = str(h.get("id") or "?")
    a = h.get("attach")
    if not isinstance(a, dict):
        return ["%s: attach must be an object" % hid]
    out: list[str] = []
    if h.get("role") != HARNESS_ROLE:
        out.append("%s: attach only allowed on role=harness rows" % hid)
    for key in ATTACH_KEYS:
        if key not in a:
            out.append("%s: attach.%s missing" % (hid, key))
    for key in ("session_id", "label", "script"):
        if key in a and not (isinstance(a[key], str) and a[key].strip()):
            out.append("%s: attach.%s must be a non-empty string" % (hid, key))
    if not (h.get("detect") or []):
        out.append("%s: attach requires non-empty detect[] (binary names)" % hid)
    if "bin_fallbacks" in a and not isinstance(a["bin_fallbacks"], list):
        out.append("%s: attach.bin_fallbacks must be a list" % hid)
    if "next_install" in a and a["next_install"] is not None and not isinstance(a["next_install"], str):
        out.append("%s: attach.next_install must be string or null" % hid)
    cfg = a.get("config_dir")
    if "config_dir" in a and cfg is not None:
        if not isinstance(cfg, dict) or not cfg.get("env") or not cfg.get("default"):
            out.append("%s: attach.config_dir must be null or {env, default}" % hid)
    return out


def validate(toolsets: dict | None = None, harnesses: dict | None = None, root_dir: Path | None = None) -> list[str]:
    """Shape problems as strings; empty list means well-formed."""
    toolsets = toolsets if toolsets is not None else load_toolsets(root_dir)
    harnesses = harnesses if harnesses is not None else load_harnesses(root_dir)
    hids = [str(h["id"]) for h in (harnesses.get("harnesses") or []) if isinstance(h, dict) and h.get("role") == HARNESS_ROLE and h.get("id")]
    problems: list[str] = []
    if not hids:
        problems.append("harnesses.json: no rows with role=harness")
    for h in harnesses.get("harnesses") or []:
        if isinstance(h, dict) and "attach" in h:
            problems.extend(_validate_attach(h))
    rows = toolsets.get("toolsets")
    if not isinstance(rows, list) or not rows:
        return problems + ["toolsets.json: toolsets[] empty or missing"]
    seen: set[str] = set()
    for t in rows:
        if not isinstance(t, dict):
            problems.append("toolsets.json: non-object row")
            continue
        tid = str(t.get("id") or "")
        if not tid:
            problems.append("toolsets.json: row without id")
            continue
        if tid in seen:
            problems.append("%s: duplicate id" % tid)
        seen.add(tid)
        for key in ("title", "provides", "lanes", "implementation"):
            if key not in t:
                problems.append("%s: missing %s" % (tid, key))
        if "catalog_tool" not in t:
            problems.append("%s: missing catalog_tool (use null when there is no row)" % tid)
        elif t.get("catalog_tool") is not None and not isinstance(t.get("catalog_tool"), str):
            problems.append("%s: catalog_tool must be string or null" % tid)
        lanes = t.get("lanes") or []
        if not isinstance(lanes, list) or not lanes or any(l not in LANES for l in lanes):
            problems.append("%s: lanes must be non-empty subset of %s" % (tid, list(LANES)))
        prov = t.get("provides") or {}
        if not isinstance(prov, dict):
            problems.append("%s: provides must be an object" % tid)
        else:
            for key in ("env", "mcp_servers", "commands"):
                if not isinstance(prov.get(key), list):
                    problems.append("%s: provides.%s must be a list" % (tid, key))
            if "brief" not in prov:
                problems.append("%s: provides.brief missing (use null)" % tid)
        impl = t.get("implementation") or {}
        if not isinstance(impl, dict):
            problems.append("%s: implementation must be an object" % tid)
            continue
        for hid in hids:
            cell = impl.get(hid)
            if not isinstance(cell, dict):
                problems.append("%s x %s: missing cell" % (tid, hid))
                continue
            if cell.get("status") not in STATUSES:
                problems.append("%s x %s: status %r not in %s" % (tid, hid, cell.get("status"), list(STATUSES)))
            if not str(cell.get("how") or "").strip():
                problems.append("%s x %s: empty how" % (tid, hid))
        for hid in impl:
            if hid not in hids:
                problems.append("%s: implementation names unknown harness %r" % (tid, hid))
    return problems
