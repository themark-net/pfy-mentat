extra_tools(want)
        if not ok:
            return {"ok": False, "live": "FAIL", "copy": "FAIL extra tools", "error": err, "id": "extra-tools"}
        st["tools_mode"] = "local_tools" if want else "split"
        save_tools_state(st)
        copy = "ON extra tools" if want else "OFF extra tools"
        return {"ok": True, "live": "PASS", "copy": copy, "id": "extra-tools", "on": want, "tools": st}
    return {"ok": False, "live": "FAIL", "copy": "FAIL tools", "error": "unknown toggle", "id": tid}

def start_sidecar(hid):
    """Spawn grok/opencode as a separate process. OpenCode uses the live local endpoint."""
    hid = (hid or "").strip()
    if not hid:
        hid = active_harness("grok")
    cur = active_harness("grok")
    if cur in STUB_ALWAYS:
        return {
            "ok": False, "id": hid, "live": "FAIL", "copy": GROK_USE,
            "error": f"{cur} is active — no grok/opencode fallback",
        }
    if hid in STUB_ALWAYS:
        return {
            "ok": False, "id": hid, "live": "FAIL", "copy": GROK_USE,
            "error": f"{hid} is not startable from the window",
        }
    if hid not in SIDECAR_OK:
        return {
            "ok": False, "id": hid, "live": "FAIL", "copy": GROK_USE,
            "error": f"{hid} is not a sidecar",
        }
    STATE.mkdir(parents=True, exist_ok=True)
    if hid == "grok":
        return start_monitor_sidecar()
    if hid == "opencode":
        bin_path = which_bin("opencode", "opencode-cli")
        stub = opencode_stub_line()
        if not bin_path:
            return {
                "ok": False, "id": hid, "live": "FAIL", "copy": stub,
                "error": "opencode missing",
            }
        base, _det = live_openai_base()
        if not base:
            return {
                "ok": False, "id": hid, "live": "FAIL", "copy": stub,
                "error": "no live local endpoint",
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
        if TOOLS_ENV.is_file():
            for line in TOOLS_ENV.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if s.startswith("export "):
                    s = s[7:].strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
        env["GROK_HOME"] = str(grok_home())
        log = STATE / "sidecar-opencode.log"
        with log.open("ab") as f:
            proc = subprocess.Popen(
                [bin_path],
                cwd=str(ROOT),
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        if not pid_alive(proc.pid):
            err = ""
            try:
                err = log.read_text(encoding="utf-8", errors="replace")[-400:]
            except Exception:
                err = "opencode exited"
            return {
                "ok": False, "id": hid, "live": "FAIL", "copy": stub,
                "error": err or "opencode exited", "pid": proc.pid, "log": str(log),
            }
        record_sidecar_pid("opencode", proc.pid)
  