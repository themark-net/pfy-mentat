#!/usr/bin/env python3
"""Enterable OpenCode open_enterable -- cite #162 (b) / #181."""
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
resolve_enterable_pid = _a.resolve_enterable_pid

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
    """Attach OpenCode + open/focus enterable terminal session. Cite #162/#171/#181.

    Re-probes FreeToken-first detect immediately before open (#171).
    Explicit :1919 FreeToken probe forces session env even if parent had
    Ollama pin or detect briefly lags (#181).
    ok=True with session_reach only when a real enterable surface is up
    against the live detect base (not a stale Launch/Ollama pin alone).
    Tracks the real terminal/session pid (not a short-lived wrapper).
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
    base, det = live_openai_base()
    status = str((det or {}).get("status") or "").strip().lower()
    engine = str((det or {}).get("engine") or "").strip() or "none"
    # #181: explicit FreeToken :1919 probe -- wins over parent Ollama pin / detect lag
    try:
        import urllib.request
        ft_ok = False
        for path in ("http://127.0.0.1:1919/v1/models", "http://127.0.0.1:1919/health"):
            try:
                req = urllib.request.Request(path, method="GET")
                with urllib.request.urlopen(req, timeout=1) as r:
                    if 200 <= int(getattr(r, "status", 200) or 200) < 300:
                        ft_ok = True
                        break
            except Exception:
                continue
        if ft_ok:
            base = "http://127.0.0.1:1919/v1"
            engine = "freetoken"
            status = "ready"
            if isinstance(det, dict):
                det = dict(det)
                det["engine"] = "freetoken"
                det["status"] = "ready"
                det["base_url"] = "http://127.0.0.1:1919"
    except Exception:
        pass
    if base:
        b = str(base).rstrip("/")
        if not b.endswith("/v1"):
            b = b + "/v1"
        base = b
    next_step = "Launch env or ./pfy up"
    if not base or status != "ready":
        clear_session_reach(STATE)
        reason = "no local engine" if status != "ready" else "no live local endpoint"
        copy = "FAIL attach -- %s \u00b7 %s" % (reason, next_step)
        return {
            "ok": False,
            "id": hid,
            "live": "FAIL",
            "copy": copy,
            "error": reason,
            "session_reach": "FAIL",
            "next_step": next_step,
            "next_steps": [{"id": "next", "label": next_step, "value": next_step}],
            "engine": engine,
            "detect_status": status or "missing",
        }

    attach_base_path = STATE / "opencode-attach-base"
    prev_base = ""
    try:
        if attach_base_path.is_file():
            prev_base = attach_base_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        prev_base = ""

    # Reuse only when still alive AND bound to the same FreeToken-first detect base (#171).
    # If FreeToken now preferred and prior session was Ollama (or base drifted), clear and re-spawn.
    term_pid = read_terminal_pid(STATE)
    real = resolve_enterable_pid(bin_path, term_pid, pid_alive) if term_pid else 0
    if real and pid_alive(real) and prev_base and prev_base != base:
        clear_session_reach(STATE)
        try:
            if attach_base_path.is_file():
                attach_base_path.unlink()
        except OSError:
            pass
        real = 0
        term_pid = 0
    if real and pid_alive(real) and prev_base == base:
        focused = _focus_pid(real)
        write_session_reach(STATE, SESSION_REACH_OK)
        write_terminal_pid(STATE, real)
        if active_harness_setter:
            active_harness_setter("opencode")
        record_last_verb("start opencode")
        return {
            "ok": True,
            "id": hid,
            "live": "READY",
            "pid": real,
            "sidecar": True,
            "session_reach": SESSION_REACH_OK,
            "focused": bool(focused),
            "copy": "attached opencode pid %s \u00b7 %s \u00b7 %s" % (real, SESSION_REACH_OK, engine),
            "error": "",
            "base_url": base,
            "engine": engine,
        }

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
    # #171/#181: FreeToken-first detect base wins over tools-model.env / stale shell Ollama pin
    env["LOCAL_OPENAI_BASE_URL"] = base
    env["OPENAI_BASE_URL"] = base
    env["GROK_HOME"] = str(grok_home())
    log = STATE / "sidecar-opencode.log"
    ok, pid, err = spawn_terminal_opencode(bin_path, str(ROOT), env, log, pid_alive)
    # Resolve again -- wrapper may have exited; opencode may still be live
    real = resolve_enterable_pid(bin_path, pid if ok else 0, pid_alive)
    if real and pid_alive(real):
        focused = _focus_pid(real)
        record_sidecar_pid("opencode", real)
        write_terminal_pid(STATE, real)
        write_session_reach(STATE, SESSION_REACH_OK)
        if active_harness_setter:
            active_harness_setter("opencode")
        else:
            try:
                (STATE / "active-harness").write_text("opencode\n", encoding="utf-8")
            except OSError:
                pass
        record_last_verb("start opencode")
        try:
            STATE.mkdir(parents=True, exist_ok=True)
            attach_base_path.write_text(base + "\n", encoding="utf-8")
        except OSError:
            pass
        return {
            "ok": True,
            "id": hid,
            "live": "READY",
            "pid": real,
            "sidecar": True,
            "log": str(log),
            "base_url": base,
            "model": model,
            "session_reach": SESSION_REACH_OK,
            "focused": bool(focused),
            "copy": "attached opencode pid %s \u00b7 %s \u00b7 %s" % (real, SESSION_REACH_OK, engine),
            "error": "",
            "engine": engine,
        }
    clear_session_reach(STATE)
    try:
        if attach_base_path.is_file():
            attach_base_path.unlink()
    except OSError:
        pass
    return {
        "ok": False,
        "id": hid,
        "live": "FAIL",
        "copy": "FAIL open session -- " + (err or "terminal cannot start"),
        "error": err or "terminal cannot start",
        "session_reach": "FAIL",
        "pid": "",
        "log": str(log),
        "base_url": base,
        "model": model,
    }
