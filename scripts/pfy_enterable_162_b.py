#!/usr/bin/env python3
"""Enterable OpenCode open_enterable — cite #162 (b)."""
from __future__ import annotations

import os
import importlib.util
from pathlib import Path

def _load_a():
    path = Path(__file__).resolve().parent / "pfy_enterable_162_a.py"
    spec = importlib.util.spec_from_file_location("pfy_enterable_162_a", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_a = _load_a()
SESSION_REACH_OK = _a.SESSION_REACH_OK
SESSION_FILE = _a.SESSION_FILE
read_session_reach = _a.read_session_reach
write_session_reach = _a.write_session_reach
clear_session_reach = _a.clear_session_reach
spawn_terminal_opencode = _a.spawn_terminal_opencode
_focus_pid = _a._focus_pid
write_terminal_pid = _a.write_terminal_pid
read_terminal_pid = _a.read_terminal_pid

def open_enterable_opencode_session(
    *,
    ROOT,
    STATE,
    which_bin,
    live_openai_base,
    inspect_models,
    write_opencode_config,
    load_tools_state,
    apply_skills_dir,
    grok_home,
    TOOLS_ENV,
    record_sidecar_pid,
    record_last_verb,
    pid_alive,
    active_harness_setter=None,
    stub_line="",
):
    """Attach OpenCode + open/focus enterable terminal session. Cite #162.

    ok=True with session_reach only when a real enterable surface is up.
    Headless sidecar alone is NOT enterable.
    """
    ROOT = Path(ROOT)
    STATE = Path(STATE)
    hid = "opencode"
    stub = stub_line or "./pfy start opencode"
    bin_path = which_bin("opencode", "opencode-cli")
    if not bin_path:
        clear_session_reach(STATE)
        return {
            "ok": False,
            "id": hid,
            "live": "FAIL",
            "copy": stub,
            "error": "opencode missing",
            "session_reach": "FAIL",
        }
    base, _det = live_openai_base()
    if not base:
        clear_session_reach(STATE)
        return {
            "ok": False,
            "id": hid,
            "live": "FAIL",
            "copy": stub,
            "error": "no live local endpoint",
            "session_reach": "FAIL",
        }

    # Only reuse a previously recorded *terminal* pid if we can focus its window.
    term_pid = read_terminal_pid(STATE)
    if term_pid and pid_alive(term_pid) and _focus_pid(term_pid):
        write_session_reach(STATE, SESSION_REACH_OK)
        if active_harness_setter:
            active_harness_setter("opencode")
        record_last_verb("start opencode")
        return {
            "ok": True,
            "id": hid,
            "live": "READY",
            "pid": term_pid,
            "sidecar": True,
            "session_reach": SESSION_REACH_OK,
            "focused": True,
            "copy": "attached opencode pid %s · %s" % (term_pid, SESSION_REACH_OK),
            "error": "",
            "base_url": base,
        }

    # Headless sidecar-opencode.pid alone is NOT enterable — do not paint PASS.
    # Always spawn/focus a real terminal below.

    models = inspect_models(base)
    cfg_path, model = write_opencode_config(base, models)
    skills = ROOT / "bootstrap" / "grok-cli" / "skills"
    env = os.environ.copy()
    env["LOCAL_OPENAI_BASE_URL"] = base
    env["OPENAI_BASE_URL"] = base
    env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY") or "local"
    env["OPENCODE_CONFIG"] = str(cfg_path)
    tst = load_tools_state()
    dest, _enabled = apply_skills_dir(tst)
    if dest is not None:
        env["OPENCODE_SKILLS"] = str(dest)
    elif skills.is_dir():
        env["OPENCODE_SKILLS"] = str(skills)
    env["TOOLS_MODE"] = str(tst.get("tools_mode") or "split")
    env["WRITE_GUARD_MODE"] = "enforce" if tst.get("write_guard") else "off"
    env["PFY_MCP"] = "1" if tst.get("mcp") else "0"
    tools_env = Path(TOOLS_ENV) if TOOLS_ENV else None
    if tools_env and tools_env.is_file():
        for line in tools_env.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s.startswith("export "):
                s = s[7:].strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            env[k.strip()] = v.strip().strip("'\"")
    env["GROK_HOME"] = str(grok_home())
    log = STATE / "sidecar-opencode.log"
    ok, pid, err = spawn_terminal_opencode(bin_path, str(ROOT), env, log, pid_alive)
    if not ok or not pid:
        clear_session_reach(STATE)
        return {
            "ok": False,
            "id": hid,
            "live": "FAIL",
            "copy": "FAIL open session — " + (err or "terminal cannot start"),
            "error": err or "terminal cannot start",
            "session_reach": "FAIL",
            "pid": "",
            "log": str(log),
            "base_url": base,
            "model": model,
        }
    # Require enterable evidence: process alive and/or focusable window
    focused = _focus_pid(pid)
    if not pid_alive(pid) and not focused:
        clear_session_reach(STATE)
        return {
            "ok": False,
            "id": hid,
            "live": "FAIL",
            "copy": "FAIL open session — terminal did not stay open",
            "error": "terminal did not stay open",
            "session_reach": "FAIL",
            "pid": "",
            "log": str(log),
            "base_url": base,
            "model": model,
        }
    record_sidecar_pid("opencode", pid)
    write_terminal_pid(STATE, pid)
    write_session_reach(STATE, SESSION_REACH_OK)
    if active_harness_setter:
        active_harness_setter("opencode")
    else:
        try:
            (STATE / "active-harness").write_text("opencode\n", encoding="utf-8")
        except OSError:
            pass
    record_last_verb("start opencode")
    return {
        "ok": True,
        "id": hid,
        "live": "READY",
        "pid": pid,
        "sidecar": True,
        "log": str(log),
        "base_url": base,
        "model": model,
        "session_reach": SESSION_REACH_OK,
        "focused": bool(focused),
        "copy": "attached opencode pid %s · %s" % (pid, SESSION_REACH_OK),
        "error": "",
    }
