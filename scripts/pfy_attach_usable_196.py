#!/usr/bin/env python3
"""Attach Hermes developer-usable session -- cite #196.

Mirrors OpenCode attach-usable (#193): FreeToken-first re-probe, child
LOCAL_OPENAI_BASE_URL / OPENAI_BASE_URL, models list + one smoke before
ok:True / READY paint. Failures honest FAIL+next, usable:false.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import urllib.request
from pathlib import Path

SESSION_FILE = "hermes-session-reach"
TERMINAL_PID_FILE = "hermes-terminal.pid"
ATTACH_BASE_FILE = "hermes-attach-base"
SESSION_REACH_OK = "terminal \u00b7 Hermes \u00b7 models \u00b7 smoke"


def _load_193():
    path = Path(__file__).resolve().parent / "pfy_attach_usable_193.py"
    spec = importlib.util.spec_from_file_location("pfy_attach_usable_193", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_162_a():
    path = Path(__file__).resolve().parent / "pfy_enterable_162_a.py"
    spec = importlib.util.spec_from_file_location("pfy_enterable_162_a_196", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_u = _load_193()
_a = _load_162_a()
prove_developer_usable = _u.prove_developer_usable
openai_compat_root = _u.openai_compat_root
spawn_terminal_opencode = _a.spawn_terminal_opencode
_focus_pid = _a._focus_pid


def _apply_opencontext_env(env):
    """Handoff OpenContext store env into Attach Hermes child. Cite #205."""
    path = Path(__file__).resolve().parent / "pfy_opencontext_205.py"
    if not path.is_file():
        return env
    spec = importlib.util.spec_from_file_location("pfy_opencontext_205_196", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.apply_child_env(env)


resolve_enterable_pid = _a.resolve_enterable_pid


def read_session_reach(STATE) -> str:
    path = Path(STATE) / SESSION_FILE
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()[:80]
    except OSError:
        return ""


def write_session_reach(STATE, text: str) -> None:
    STATE = Path(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / SESSION_FILE).write_text((text or "").strip()[:80] + "\n", encoding="utf-8")


def clear_session_reach(STATE) -> None:
    STATE = Path(STATE)
    for name in (SESSION_FILE, TERMINAL_PID_FILE, ATTACH_BASE_FILE):
        path = STATE / name
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def write_terminal_pid(STATE, pid: int) -> None:
    STATE = Path(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / TERMINAL_PID_FILE).write_text(str(int(pid)) + "\n", encoding="utf-8")


def read_terminal_pid(STATE):
    path = Path(STATE) / TERMINAL_PID_FILE
    if not path.is_file():
        return 0
    try:
        return int(path.read_text(encoding="utf-8", errors="replace").strip())
    except (ValueError, OSError):
        return 0


def live_session_reach(STATE, pid_alive=None) -> str:
    """Return Hermes session reach only if enterable pid is still alive. Cite #196."""
    reach = read_session_reach(STATE)
    if not reach or reach in ("FAIL", "SKIP"):
        return reach if reach in ("FAIL", "SKIP") else ""
    pid = read_terminal_pid(STATE)
    alive = False
    if pid and callable(pid_alive):
        alive = bool(pid_alive(pid))
    elif pid:
        try:
            os.kill(int(pid), 0)
            alive = True
        except OSError:
            alive = False
    if not alive:
        clear_session_reach(STATE)
        return ""
    return reach


def fail_not_usable(STATE, hid, reason, next_step, engine, status, base="", model=""):
    clear_session_reach(STATE)
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
        "base_url": base,
        "model": model,
        "usable": False,
    }


def _probe_freetoken(base, det):
    """Explicit :1919 FreeToken probe -- wins over parent Ollama pin / detect lag (#171/#181)."""
    engine = str((det or {}).get("engine") or "").strip() or "none"
    status = str((det or {}).get("status") or "").strip().lower()
    try:
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
    return base, det, engine, status


def inspect_models(base_url):
    """CLI/prove inspect -- strip trailing /v1 like #187/#193."""
    if not base_url:
        return []
    base = openai_compat_root(base_url)
    ids, seen = [], set()
    for path in ("/v1/models", "/api/tags"):
        try:
            req = urllib.request.Request(base + path, method="GET")
            with urllib.request.urlopen(req, timeout=2) as r:
                d = json.loads(r.read().decode() or "{}")
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for m in d.get("data") or []:
            name = (m.get("id") or m.get("name") or "") if isinstance(m, dict) else str(m)
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name)
                ids.append(name)
        for m in d.get("models") or []:
            name = (m.get("name") or m.get("model") or m.get("id") or "") if isinstance(m, dict) else str(m)
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name)
                ids.append(name)
    return ids


def open_enterable_hermes_session(
    *,
    ROOT,
    STATE,
    which_bin,
    live_openai_base,
    inspect_models,
    record_sidecar_pid,
    record_last_verb,
    pid_alive,
    active_harness_setter=None,
    stub_line="",
):
    """Attach Hermes + open/focus enterable terminal. Cite #196.

    Re-probes FreeToken-first detect immediately before open (#171/#181).
    ok=True with session_reach only when a real enterable surface is up
    against the live detect base AND models list + one smoke succeed (#196).
    Child env inherits LOCAL_OPENAI_BASE_URL / OPENAI_BASE_URL.
    """
    ROOT = Path(ROOT)
    STATE = Path(STATE)
    hid = "hermes"
    stub = stub_line or "./pfy start hermes"
    bin_path = which_bin("hermes", "hermes-agent")
    if not bin_path:
        clear_session_reach(STATE)
        return {
            "ok": False,
            "id": hid,
            "live": "FAIL",
            "copy": stub,
            "error": "hermes missing",
            "session_reach": "FAIL",
            "usable": False,
        }
    base, det = live_openai_base()
    base, det, engine, status = _probe_freetoken(base, det)
    next_step = "Launch env or ./pfy up"
    if not base or status != "ready":
        reason = "no local engine" if status != "ready" else "no live local endpoint"
        return fail_not_usable(STATE, hid, reason, next_step, engine, status, base=base)

    attach_base_path = STATE / ATTACH_BASE_FILE
    prev_base = ""
    try:
        if attach_base_path.is_file():
            prev_base = attach_base_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        prev_base = ""

    term_pid = read_terminal_pid(STATE)
    real = resolve_enterable_pid(bin_path, term_pid, pid_alive) if term_pid else 0
    if real and pid_alive(real) and prev_base and prev_base != base:
        clear_session_reach(STATE)
        real = 0
        term_pid = 0
    if real and pid_alive(real) and prev_base == base:
        usable_ok, model, usable_err = prove_developer_usable(base, inspect_models)
        if not usable_ok:
            return fail_not_usable(
                STATE, hid, usable_err or "session not usable", next_step,
                engine, status, base=base, model=model,
            )
        focused = _focus_pid(real)
        write_session_reach(STATE, SESSION_REACH_OK)
        write_terminal_pid(STATE, real)
        if active_harness_setter:
            active_harness_setter("hermes")
        record_last_verb("start hermes")
        return {
            "ok": True,
            "id": hid,
            "live": "READY",
            "pid": real,
            "sidecar": True,
            "session_reach": SESSION_REACH_OK,
            "focused": bool(focused),
            "copy": "attached hermes pid %s \u00b7 %s \u00b7 %s" % (real, SESSION_REACH_OK, engine),
            "error": "",
            "base_url": base,
            "engine": engine,
            "model": model,
            "usable": True,
            "models_ok": True,
            "smoke_ok": True,
        }

    env = os.environ.copy()
    env["LOCAL_OPENAI_BASE_URL"] = base
    env["OPENAI_BASE_URL"] = base
    env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY") or "local"
    _apply_opencontext_env(env)
    log = STATE / "sidecar-hermes.log"
    ok, pid, err = spawn_terminal_opencode(bin_path, str(ROOT), env, log, pid_alive)
    if err:
        err = str(err).replace("OpenCode", "Hermes")
    real = resolve_enterable_pid(bin_path, pid if ok else 0, pid_alive)
    if real and pid_alive(real):
        usable_ok, smoke_model, usable_err = prove_developer_usable(base, inspect_models)
        if not usable_ok:
            return fail_not_usable(
                STATE, hid, usable_err or "session not usable", next_step,
                engine, status, base=base, model=smoke_model,
            )
        focused = _focus_pid(real)
        record_sidecar_pid("hermes", real)
        write_terminal_pid(STATE, real)
        write_session_reach(STATE, SESSION_REACH_OK)
        if active_harness_setter:
            active_harness_setter("hermes")
        else:
            try:
                (STATE / "active-harness").write_text("hermes\n", encoding="utf-8")
            except OSError:
                pass
        record_last_verb("start hermes")
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
            "model": smoke_model,
            "session_reach": SESSION_REACH_OK,
            "focused": bool(focused),
            "copy": "attached hermes pid %s \u00b7 %s \u00b7 %s" % (real, SESSION_REACH_OK, engine),
            "error": "",
            "engine": engine,
            "usable": True,
            "models_ok": True,
            "smoke_ok": True,
        }
    clear_session_reach(STATE)
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
        "usable": False,
        "next_step": next_step,
    }


def prove_cli(base):
    """CLI prove: models list + one smoke. Exit 0 only when usable. Cite #196."""
    next_step = "Launch env or ./pfy up"
    base = str(base or "").strip()
    if not base:
        print("FAIL attach -- no live local endpoint \u00b7 %s" % next_step)
        print("  equiv: ./pfy models")
        return 1
    ok, model, err = prove_developer_usable(base, inspect_models)
    if not ok:
        print("FAIL attach -- %s \u00b7 %s" % (err or "session not usable", next_step))
        print("  equiv: ./pfy models")
        return 1
    print("PASS prove \u00b7 %s \u00b7 models \u00b7 smoke" % (model or "local"))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--prove"]:
        raise SystemExit(prove_cli(args[1] if len(args) > 1 else os.environ.get("LOCAL_OPENAI_BASE_URL") or ""))
    print("usage: pfy_attach_usable_196.py --prove [BASE]", file=sys.stderr)
    raise SystemExit(2)
