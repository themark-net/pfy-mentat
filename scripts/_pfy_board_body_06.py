)

def which_bin(*names):
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    return ""


def _load_enterable_162():
    """Load pfy_enterable_162 or return (None, error). Cite #162."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_enterable_162.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_enterable_162", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _session_reach_live():
    mod, err = _load_enterable_162()
    if mod is None:
        return ""
    try:
        return mod.read_session_reach(STATE) or ""
    except Exception:
        return ""

def open_enterable_opencode_session():
    """Attach + open/focus enterable OpenCode terminal. Cite #162."""
    mod, err = _load_enterable_162()
    stub = opencode_stub_line()
    if mod is None:
        return {
            "ok": False, "id": "opencode", "live": "FAIL", "copy": stub,
            "error": err or "enterable module missing", "session_reach": "FAIL",
        }
    def _set_active(hid):
        (STATE / "active-harness").write_text(str(hid) + "\n", encoding="utf-8")
    return mod.open_enterable_opencode_session(
        ROOT=ROOT, STATE=STATE, which_bin=which_bin,
        live_openai_base=live_openai_base, inspect_models=inspect_models,
        write_opencode_config=write_opencode_config, load_tools_state=load_tools_state,
        apply_skills_dir=apply_skills_dir, grok_home=grok_home, TOOLS_ENV=TOOLS_ENV,
        record_sidecar_pid=record_sidecar_pid, record_last_verb=record_last_verb,
        pid_alive=pid_alive, active_harness_setter=_set_active, stub_line=stub,
    )


def pid_alive(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def live_openai_base():
    det = detector_json()
    base = str(det.get("base_url") or os.environ.get("LOCAL_OPENAI_BASE_URL") or "").strip()
    if base == "(none)":
        base = ""
    if not base:
        return "", det
    b = base.rstrip("/")
    if not b.endswith("/v1"):
        b = b + "/v1"
    return b, det


def write_opencode_config(base, models):
    STATE.mkdir(parents=True, exist_ok=True)
    name = ""
    if models:
        name = str(models[0]).strip()
    if not name:
        name = (os.environ.get("LOCAL_CODER_MODEL") or os.environ.get("PFY_FT_MODEL") or os.environ.get("PFY_OLLAMA_MODEL") or "local").strip() or "local"
    opts = {}
    opts["baseURL"] = base
    opts["apiKey"] = "local"
    localp = {}
    localp["name"] = "local"
    localp["options"] = opts
    localp["models"] = {name: {"name": name}}
    localp["npm"] = "@ai-sdk/openai-compatible"
    cfg = {"provider": {"local": localp}, "model": "local/" + name}
    tst = load_tools_state()
    tools_name = local_tools_model()
    if (tst.get("tools_mode") or "") == "local_tools" and tools_name:
        name = tools_name
        localp["models"][name] = {"name": name}
        cfg["model"] = "local/" + name
    mcp = {}
    if tst.get("mcp"):
        mcp["codebase-memory"] = {"type": "local", "command": ["codebase-memory-mcp"], "enabled": True}
    if tst.get("write_guard"):
        wg = write_guard_root()
        src = str((wg / "src") if wg else "")
        mcp["write-guard"] = {
            "type": "local",
            "command": ["python3", "-m", "write_guard", "serve"],
            "enabled": True,
            "environment": {
                "WRITE_GUARD_MODE": "enforce",
                "WRITE_GUARD_ROOTS": str(ROOT),
                "PYTHONPATH": src,
            },
        }
    if mcp:
        cfg["mcp"] = mcp
    path = STATE / "opencode.json"
    path.write_text(json.dumps(cfg, indent=2) + chr(10