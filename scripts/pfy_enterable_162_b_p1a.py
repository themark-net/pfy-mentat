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
    """Attach OpenCode + open/focus enterable terminal session. Cite #162/#171/#181/#193.

    Re-probes FreeToken-first detect immediately before open (#171).
    Explicit :1919 FreeToken probe forces session env even if parent had
    Ollama pin or detect briefly lags (#181).
    ok=True with session_reach only when a real enterable surface is up
    against the live detect base AND models list + one smoke succeed (#193).
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
