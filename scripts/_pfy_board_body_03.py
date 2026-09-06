xt = pfy_status_stdout()
    parsed = parse_status(status_text)
    parsed_chips = {c["id"]: c for c in parsed["chips"]}
    chips = []
    for h in harnesses:
        hid = str(h.get("id") or "")
        if not hid:
            continue
        parsed_row = parsed_chips.get(hid)
        live = honest_live(parsed_row.get("live") if parsed_row else "missing")
        issue = h.get("github_issue")
        rec = {
            "id": hid, "name": h.get("name") or hid, "role": h.get("role") or "",
            "live": live, "issue_url": f"{ISSUE_BASE}{issue}" if issue not in (None, "") else "",
            "one_liner": one_liner(hid, h),
            "startable": live == "ready" and hid in SIDECAR_OK,
        }
        if hid in STUB_ALWAYS:
            rec["startable"] = False
            rec["one_liner"] = GROK_USE
        if hid == "grok":
            rec["live"] = grok_path_live()
            rec["startable"] = rec["live"] == "ready"
        chips.append(rec)
    procs = process_table()
    verb = last_verb()
    active = parsed.get("active") or active_harness(default)
    live_active = next((c["live"] for c in chips if c["id"] == active), "missing")
    host = socket.gethostname()
    is_nimo = "nimo" in host.lower()
    profile = deploy_profile()
    base = det.get("base_url") or (parsed.get("runtime") or {}).get("base_url") or ""
    if base == "(none)":
        base = ""
    eng = det.get("engine") or ""
    eng_norm = ENGINE_ALIAS.get(eng, eng)
    ready_h = any(c["role"] == "harness" and c["live"] == "ready" for c in chips)
    modes = []
    order = []
    for hid, label, port in DETECT_ORDER:
        live = honest_live(next((c["live"] for c in chips if c["id"] == hid), "missing"))
        order.append({"id": hid, "label": label, "port": port, "live": live, "winner": eng_norm == hid,
                      "one_liner": one_liner(hid, next((h for h in harnesses if h.get("id") == hid), {}))})
    winner = next((o for o in order if o["winner"]), None)
    engine_live = honest_live((winner["live"] if winner else "") or det.get("status") or "missing")
    msgs = org_messages()
    nimo_note = ""
    usage_info = local_usage_info()
    tape = tape_steps(det, verb, usage_info.get("lines") or parsed.get("usage") or [], active, live_active)
    tape_outcome = " then ".join(f"{t['label']} {t['live']}" for t in tape)
    env_stage_live = next((t["live"] for t in tape if t["id"] == "env-stage"), "SKIP")
    blocked_reason = GROK_USE if active in STUB_ALWAYS else ""
    try:
        import importlib.util as _ilu
        _up = ROOT / "scripts" / "pfy_usage_165.py"
        _sr = dict(parsed.get("runtime") or {})
        if _up.is_file():
            _sp = _ilu.spec_from_file_location("pfy_usage_165", _up)
            _um = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_um)
            _sr = _um.enrich_status_runtime(_sr, usage_info)
        else:
            _sr = dict(_sr)
            _sr["tok_path"] = usage_info.get("tok_path") or "SKIP"
            _sr["vram"] = usage_info.get("vram") or "SKIP"
    except Exception:
        _sr = dict(parsed.get("runtime") or {})
        _sr["tok_path"] = usage_info.get("tok_path") or "SKIP"
        _sr["vram"] = usage_info.get("vram") or "SKIP"
    models = list(usage_info.get("models") or []) or (inspect_models(base) if base else [])
    if usage_info.get("endpoint"):
        base = usage_info.get("endpoint") or base
    return {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": host, "root": str(ROOT), "profile": profile, "local_only": profile == "local-only",
        "is_nimo": is_nimo,
        "detector": det, "status_runtime": _sr, "usage": usage_info,
        "chips": chips, "active": active, "last_verb": verb, "now": now_state(active, live_active, procs, verb),
        "processes": procs, "detect_order": order, "engine_live": engine_live,
        "models": models,
        "models_note": "",
        "org_messages": msgs, "agent_lane_collapsed": not msgs,
        "honest": {"modes": modes, "note_nimo": nimo_note},
        "grok_chip_note": "",
        "midline": "",
        "tape": tape, "tape_outcome": tape_outcome, "env_stage_live": env_stage_live,
        "blocked_copy": GROK_USE, "blocked_reason": blocked_reason,
        "status_stdout": status_text, "no_daemon": True,
        "active_stub": active in STUB_ALWAYS, "refresh_ms": REFRESH_MS,
        "sidecar_ok": sorted(SIDECAR_OK),
        "sidecar_pid": sidecar_pid_live(),
        "session_reach": _session_reach_live(),
        "grok_path": grok_path_live(),
        "monitor_note": last_monitor_note(),
        "monitor_pid": monitor_pid_live(),
        "tools": load_tools_state(),
    }

def html_page():
    if FRONTEND.is_file():
        return FRONTEND.read_text(encoding="utf-8")
    return (
        "<!DOCTYPE html><html><body>error: gui/operator/frontend/index.html missing</body></h