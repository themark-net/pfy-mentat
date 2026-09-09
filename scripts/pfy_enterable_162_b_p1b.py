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
        # #193: reuse still requires models list + smoke -- no status-only attached paint
        usable_ok, model, usable_err = prove_developer_usable(base, inspect_models)
        if not usable_ok:
            return fail_not_usable(clear_session_reach, 
                STATE, hid, usable_err or "session not usable", next_step,
                engine, status, base=base, model=model,
            )
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
            "model": model,
            "usable": True,
            "models_ok": True,
            "smoke_ok": True,
        }

    # #193/#187: strip trailing /v1 before inspect_models (avoids /v1/v1/models)
    models = inspect_models(openai_compat_root(base))
    cfg_path, model = write_opencode_config(base, models)
    skills = ROOT / "bootstrap" / "grok-cli" / "skills"
    env = os.environ.copy()
    env["LOCAL_OPENAI_BASE_URL"] = base
    env["OPENAI_BASE_URL"] = base
    env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY") or "local"
    _apply_opencontext_env(env)
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
        # #193: prove models list + smoke before painting attached
        usable_ok, smoke_model, usable_err = prove_developer_usable(base, inspect_models)
        if not usable_ok:
            return fail_not_usable(clear_session_reach, 
                STATE, hid, usable_err or "session not usable", next_step,
                engine, status, base=base, model=smoke_model or model,
            )
        if smoke_model:
            model = smoke_model
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
            "usable": True,
            "models_ok": True,
            "smoke_ok": True,
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
        "usable": False,
    }
