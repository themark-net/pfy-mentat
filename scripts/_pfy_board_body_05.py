nv-stage. No harness exec.

    Always record_last_verb so LOOP last/timestamp refresh even when already up.
    Honest skip / already-up paints SKIP (never silent).
    """
    if not PFY.is_file():
        record_last_verb("env")
        return {"ok": False, "live": "FAIL", "copy": "FAIL env", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "env"], timeout=120.0)
    blob = out or ""
    low = blob.lower()
    # Always stamp the click so LOOP last + when move even if tape was already READY.
    record_last_verb("env")
    if rc != 0:
        return {
            "ok": False, "live": "FAIL", "copy": "FAIL env",
            "error": (blob or "env failed")[-400:],
            "stdout": blob[-800:],
        }
    # Honest skip / no local runtime: paint SKIP, not a fake PASS that looks like silence.
    if (
        "honest skip" in low
        or "no local runtime" in low
        or "skip: env-stage" in low
        or "env-stage.sh missing" in low
    ):
        return {"ok": True, "live": "SKIP", "copy": "SKIP env", "stdout": blob[-800:]}
    return {
        "ok": True, "live": "PASS", "copy": "PASS env",
        "error": "",
        "stdout": blob[-800:],
    }

def which_bin(*names):
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    return ""

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
    path.write_text(json.dumps(cfg, indent=2) + chr(10), encoding="utf-8")
    gen = ROOT / "examples" / "opencode-ollama" / ".generated" / "opencode.json"
    try:
        gen.parent.mkdir(parents=True, exist_ok=True)
        gen.write_text(json.dumps(cfg, indent=2) + chr(10), encoding="utf-8")
    except OSError:
        pass
    return path, name

def record_sidecar_pid(hid, pid):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / ("sidecar-%s.pid" % hid)).write_text(str(pid) + chr(10), encoding="utf-8")

def sidecar_pid_live():
    for hid i