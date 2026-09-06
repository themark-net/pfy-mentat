#!/usr/bin/env python3
"""Enterable OpenCode session helpers — cite #162."""
from __future__ import annotations

import importlib.util
from pathlib import Path

def _load_b():
    path = Path(__file__).resolve().parent / "pfy_enterable_162_b.py"
    spec = importlib.util.spec_from_file_location("pfy_enterable_162_b", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_b = _load_b()
SESSION_REACH_OK = _b.SESSION_REACH_OK
SESSION_FILE = _b.SESSION_FILE
read_session_reach = _b.read_session_reach
write_session_reach = _b.write_session_reach
clear_session_reach = _b.clear_session_reach
spawn_terminal_opencode = _b.spawn_terminal_opencode
open_enterable_opencode_session = _b.open_enterable_opencode_session

def arm_launch_env_session(res, open_fn) -> dict:
    """After Launch env: open/arm enterable session OR honest SKIP. Cite #162.

    Copy endpoint/status alone does not satisfy #162.
    """
    out = dict(res or {})
    live = str(out.get("live") or "")
    next_steps = list(out.get("next_steps") or [])
    # Strip any prior enterable markers
    next_steps = [s for s in next_steps if (s or {}).get("id") not in ("enterable", "session")]
    if not out.get("ok"):
        out["session_reach"] = "FAIL"
        out["enterable"] = False
        return out
    if live == "SKIP":
        # Env itself skipped — honest about enterable too
        reason = "SKIP enterable session · env skipped"
        next_steps.append({"id": "enterable", "label": reason, "value": reason})
        what = str(out.get("what") or "")
        if "enterable" not in what.lower():
            out["what"] = (what + " · " + reason).strip(" ·")
        out["session_reach"] = "SKIP"
        out["enterable"] = False
        out["next_steps"] = next_steps
        return out
    # Try to open/arm enterable OpenCode session
    try:
        sess = open_fn() if callable(open_fn) else {}
    except Exception as e:
        sess = {"ok": False, "error": str(e)[:300], "session_reach": "FAIL"}
    if sess.get("ok") and sess.get("session_reach"):
        reach = sess.get("session_reach") or SESSION_REACH_OK
        next_steps.insert(0, {
            "id": "enterable",
            "label": "session " + reach,
            "value": reach,
        })
        what = str(out.get("what") or "")
        bit = "session " + reach
        if bit not in what:
            out["what"] = (what + " · " + bit).strip(" ·")
        out["session_reach"] = reach
        out["enterable"] = True
        out["session_pid"] = sess.get("pid") or ""
        out["next_steps"] = next_steps
        # Keep env copy; append session reach
        copy = str(out.get("copy") or "PASS env")
        if "session" not in copy.lower():
            out["copy"] = copy + " · " + bit
        return out
    # Honest SKIP — cannot open enterable surface
    err = str(sess.get("error") or sess.get("copy") or "terminal cannot start")[:200]
    reason = "SKIP enterable session · " + err
    next_steps.append({"id": "enterable", "label": reason, "value": reason})
    what = str(out.get("what") or "")
    if "enterable" not in what.lower() and "session" not in what.lower():
        out["what"] = (what + " · " + reason).strip(" ·")
    out["session_reach"] = "SKIP"
    out["enterable"] = False
    out["next_steps"] = next_steps
    # Downgrade PASS env narrative? Keep env PASS/SKIP but make enterable SKIP explicit.
    copy = str(out.get("copy") or "")
    if copy.startswith("PASS"):
        out["copy"] = copy + " · " + reason
    return out

