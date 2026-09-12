if tid in ("write-guard", "write_guard"):
        ok, err = apply_write_guard(want)
        if not ok:
            return {"ok": False, "live": "FAIL", "copy": "FAIL write-guard", "error": err, "id": "write-guard"}
        st["write_guard"] = want
        save_tools_state(st)
        return {"ok": True, "live": "PASS", "copy": ("ON " if want else "OFF ") + "write-guard", "id": "write-guard", "on": want, "tools": st}
    if tid in ("extra-tools", "local_tools", "tools_mode"):
        ok, err = apply_extra_tools(want)
        if not ok:
            return {"ok": False, "live": "FAIL", "copy": "FAIL extra tools", "error": err, "id": "extra-tools"}
        st["tools_mode"] = "local_tools" if want else "split"
        save_tools_state(st)
        copy = "ON extra tools" if want else "OFF extra tools"
        return {"ok": True, "live": "PASS", "copy": copy, "id": "extra-tools", "on": want, "tools": st}
    return {"ok": False, "live": "FAIL", "copy": "FAIL tools", "error": "unknown toggle", "id": tid}

def start_sidecar(hid, mode=None):
    """Spawn grok/opencode/hermes sidecar. Grok prove-usable (#202); Hermes (#196); OpenCode (#171/#193). Mode handoff (#208)."""
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
    mmod, merr = _load_attach_mode_208()
    if mmod is None:
        return {
            "ok": False, "id": hid, "live": "FAIL", "copy": "FAIL mode -- module missing",
            "error": merr or "pfy_attach_mode_208 missing", "usable": False,
            "session_reach": "FAIL", "next_step": "./pfy setup",
        }
    prepared = mmod.prepare(ROOT, STATE, hid, mode=mode, which=which_bin)
    if not prepared.get("ok"):
        return prepared
    using = prepared.get("mode") or "bare"
    if hid == "grok":
        result = open_enterable_grok_session()
    elif hid == "opencode":
        result = open_enterable_opencode_session()
    elif hid == "hermes":
        result = open_enterable_hermes_session()
    else:
        result = None
    if result is not None:
        result = dict(result)
        result["mode"] = using
        result["using"] = using
        if result.get("ok") and result.get("usable") is not False:
            mmod.mark_live(STATE, using)
            copy = str(result.get("copy") or "")
            tag = "using: %s" % using
            if tag not in copy:
                result["copy"] = (copy + " · " + tag).strip(" ·")
        return result
    log = STATE / f"sidecar-{hid}.log"
    with log.open("ab") as f:
        proc = subprocess.Popen(
            ["bash", str(PFY), "start", hid],
            cwd=str(ROOT),
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return {"ok": True, "id": hid, "live": "READY", "pid": proc.pid, "sidecar": True, "log": str(log)}


def run_space_invaders():
    """Session proof: Attach OpenCode required, then workspace/space-invaders. Cite #155."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_space_invaders.py"
    if not path.is_file():
        return {
            "ok": False, "live": "FAIL",
            "copy": "FAIL Space Invaders · module missing",
            "error": str(path), "path": "",
        }
    spec = importlib.util.spec_from_file_location("pfy_space_invaders", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run(
        root=ROOT,
        state=STATE,
        which_bin=which_bin,
        write_opencode_config=write_opencode_config,
        live_openai_base=live_openai_base,
        inspect_models=inspect_models,
        record_last_verb=record_last_verb,
        active_harness=active_harness,
        pid_alive=pid_alive,
    )

def _load_verify_159():
    """Load pfy_verify_159 or return (None, error). Cite #159."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_verify_159.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_verify_159", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def open_space_invaders_game():
    mod, err = _load_verify_159()
    if mod is None:
        return {"ok": False, "live": "FAIL", "copy": "FAIL Open game · module missing", "error": err}
    try:
        return mod.open_game(ROOT)
    except Excep