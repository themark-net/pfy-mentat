        env["PYTHONPATH"] = str(wg / "src") + os.pathsep + env.get("PYTHONPATH", "")
        env["WRITE_GUARD_MODE"] = "enforce"
        env["WRITE_GUARD_ROOTS"] = str(ROOT)
        policy = wg / "policy.default.yaml"
        if policy.is_file():
            env["WRITE_GUARD_POLICY"] = str(policy)
        probe = ROOT / "README.md"
        if not probe.is_file():
            probe = wg / "README.md"
        try:
            p = subprocess.run(
                ["python3", "-m", "write_guard", "check", "--path", str(probe), "--op", "write", "--mode", "enforce"],
                cwd=str(ROOT), capture_output=True, text=True, timeout=20.0, env=env,
            )
            rc, out = p.returncode, (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        except (OSError, subprocess.TimeoutExpired) as e:
            rc, out = 1, str(e)
        if rc != 0:
            return False, (out or "write-guard check failed")[-300:]
        upsert_env_file(TOOLS_ENV, {"WRITE_GUARD_MODE": "enforce", "WRITE_GUARD_ROOTS": str(ROOT)})
        (STATE / "write-guard-mode").write_text("enforce\n", encoding="utf-8")
        return True, ""
    for dest in (STATE_GROK, grok_config_path()):
        patch_toml_section_enabled(dest, "mcp_servers.write-guard", False)
    upsert_env_file(TOOLS_ENV, {"WRITE_GUARD_MODE": "off"}) if TOOLS_ENV.parent.is_dir() or TOOLS_ENV.is_file() else None
    (STATE / "write-guard-mode").write_text("off\n", encoding="utf-8")
    yml = STATE / "mcp-servers.write-guard.yaml"
    if yml.is_file():
        yml.write_text(yml.read_text(encoding="utf-8").replace("enabled: true", "enabled: false"), encoding="utf-8")
    return True, ""

def apply_extra_tools(want):
    name = local_tools_model()
    mode = "local_tools" if want else "split"
    if want and not name:
        return False, "no local tools model"
    STATE.mkdir(parents=True, exist_ok=True)
    updates = {"TOOLS_MODE": mode}
    if name:
        updates["LOCAL_TOOLS_MODEL"] = name
    upsert_env_file(TOOLS_ENV, updates)
    text = TOOLS_ENV.read_text(encoding="utf-8") if TOOLS_ENV.is_file() else ""
    if ("TOOLS_MODE=" + mode) not in text.replace("export ", ""):
        return False, "tools-model.env not applied"
    if want and "LOCAL_TOOLS_MODEL=" not in text.replace("export ", ""):
        return False, "LOCAL_TOOLS_MODEL not applied"
    (STATE / "tools-mode").write_text(mode + "\n", encoding="utf-8")
    return True, ""

def set_tool(tid, on):
    tid = (tid or "").strip()
    st = load_tools_state()
    want = bool(on)
    if tid in SKILL_IDS:
        skill = SKILLS_ROOT / tid / "SKILL.md"
        if want and not skill.is_file():
            return {"ok": False, "live": "FAIL", "copy": "FAIL " + tid, "error": tid + " missing", "id": tid}
        st["skills"][tid] = want
        dest, enabled = apply_skills_dir(st)
        if dest is None:
            return {"ok": False, "live": "FAIL", "copy": "FAIL " + tid, "error": enabled, "id": tid}
        save_tools_state(st)
        copy = ("ON " if want else "OFF ") + tid
        return {"ok": True, "live": "PASS", "copy": copy, "id": tid, "on": want, "tools": st}
    if tid == "mcp":
        ok, err = apply_mcp(want)
        if not ok:
            return {"ok": False, "live": "FAIL", "copy": "FAIL mcp", "error": err, "id": tid}
        st["mcp"] = want
        save_tools_state(st)
        (STATE / "mcp-on").write_text("1\n" if want else "0\n", encoding="utf-8")
        return {"ok": True, "live": "PASS", "copy": ("ON " if want else "OFF ") + "mcp", "id": tid, "on": want, "tools": st}
    if tid in ("write-guard", "write_guard"):
        ok, err = apply_write_guard(want)
        if not ok:
            return {"ok": False, "live": "FAIL", "copy": "FAIL write-guard", "error": err, "id": "write-guard"}
        st["write_guard"] = want
        save_tools_state(st)
        return {"ok": True, "live": "PASS", "copy": ("ON " if want else "OFF ") + "write-guard", "id": "write-guard", "on": want, "tools": st}
    if 