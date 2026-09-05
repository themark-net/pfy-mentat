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
    tape = tape_steps(det, verb, parsed.get("usage") or [], active, live_active)
    tape_outcome = " then ".join(f"{t['label']} {t['live']}" for t in tape)
    env_stage_live = next((t["live"] for t in tape if t["id"] == "env-stage"), "SKIP")
    blocked_reason = GROK_USE if active in STUB_ALWAYS else ""
    return {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": host, "root": str(ROOT), "profile": profile, "local_only": profile == "local-only",
        "is_nimo": is_nimo,
        "detector": det, "status_runtime": parsed.get("runtime") or {}, "usage": parsed.get("usage") or [],
        "chips": chips, "active": active, "last_verb": verb, "now": now_state(active, live_active, procs, verb),
        "processes": procs, "detect_order": order, "engine_live": engine_live,
        "models": inspect_models(base) if base else [],
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
        "grok_path": grok_path_live(),
        "monitor_note": last_monitor_note(),
        "monitor_pid": monitor_pid_live(),
        "tools": load_tools_state(),
    }

def html_page():
    if FRONTEND.is_file():
        return FRONTEND.read_text(encoding="utf-8")
    return (
        "<!DOCTYPE html><html><body>error: gui/operator/frontend/index.html missing</body></html>"
    )



def frontend_static(path: str):
    """Serve sibling assets from gui/operator/frontend (app-core-*.js, app-ui.js, …)."""
    name = (path or "").lstrip("/")
    if not name or "/" in name or "\\" in name or ".." in name or name.startswith("."):
        return None
    if not name.endswith((".js", ".css", ".map", ".svg", ".png", ".ico", ".woff2")):
        return None
    fp = (FRONTEND_DIR / name).resolve()
    try:
        fp.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return None
    if not fp.is_file():
        return None
    ctype = {
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".map": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
        ".woff2": "font/woff2",
    }.get(fp.suffix.lower(), "application/octet-stream")
    return fp, ctype


def run_stage():
    """Run product env-stage (./pfy stage). 