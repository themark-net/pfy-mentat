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

def _load_attach_196():
    """Load pfy_attach_usable_196 or return (None, error). Cite #196."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_attach_usable_196.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_attach_usable_196", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_attach_202():
    """Load pfy_attach_usable_202 or return (None, error). Cite #202."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_attach_usable_202.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_attach_usable_202", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_attach_220():
    """Load pfy_attach_usable_220 or return (None, error). Cite #220."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_attach_usable_220.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_attach_usable_220", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_attach_221():
    """Load pfy_attach_usable_221 or return (None, error). Cite #221."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_attach_usable_221.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_attach_usable_221", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_attach_mode_208():
    """Load pfy_attach_mode_208 or return (None, error). Cite #208."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_attach_mode_208.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_attach_mode_208", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_recommend_207():
    """Load pfy_recommend_models_207 or return (None, error). Cite #207."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_recommend_models_207.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_recommend_models_207", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_catalog_209():
    """Load pfy_catalog_ask_queue_209 or return (None, error). Cite #209."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_catalog_ask_queue_209.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_catalog_ask_queue_209", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_live_org_214():
    """Load pfy_live_org_queue_214 or return (None, error). Cite #214."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_live_org_queue_214.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_live_org_queue_214", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_orchestration_213():
    """Load pfy_orchestration_213 or return (None, error). Cite #213."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_orchestration_213.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_orchestration_213", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def _load_code_graph_215():
    """Load pfy_code_graph_215 or return (None, error). Cite #215."""
    import importlib.util
    path = ROOT / "scripts" / "pfy_code_graph_215.py"
    if not path.is_file():
        return None, str(path)
    try:
        spec = importlib.util.spec_from_file_location("pfy_code_graph_215", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, ""
    except Exception as e:
        return None, str(e)[:400]

def attach_mode_fields():
    mod, err = _load_attach_mode_208()
    if mod is None:
        return {"attach_mode": "bare", "using": "bare", "attach_mode_when": "", "attach_mode_live": ""}
    try:
        return mod.snapshot_fields(STATE)
    except Exception:
        return {"attach_mode": "bare", "using": "bare", "attach_mode_when": "", "attach_mode_live": ""}

def set_attach_mode(mode):
    """Select one attach mode (bare|orchestration|code-graph). Cite #208."""
    mod, err = _load_attach_mode_208()
    if mod is None:
        return {"ok": False, "live": "FAIL", "copy": "FAIL mode -- module missing", "error": err or "missing", "usable": False, "next_step": "./pfy setup"}
    STATE.mkdir(parents=True, exist_ok=True)
    return mod.set_mode(STATE, mode)

def recommend_fields(models, eng, det, base):
    """Snapshot recommend/try fields. Cite #207. Never invent a best list."""
    empty = {
        "recommend_ok": False, "recommend": [], "recommend_ranked": [],
        "recommend_copy": "", "recommend_next": "Launch env or ./pfy up",
        "recommend_top": "", "recommend_host": {}, "pinned_model": "",
        "model_handoff": "",
    }
    mod, err = _load_recommend_207()
    if mod is None:
        empty["recommend_copy"] = "FAIL recommend -- module missing"
        empty["recommend_next"] = "./pfy setup"
        return empty
    try:
        st = str((det or {}).get("status") or "")
        return mod.snapshot_fields(
            STATE, ROOT, pulled=list(models or []), engine=eng or "",
            status=st, base=base or "",
        )
    except Exception as e:
        empty["recommend_copy"] = "FAIL recommend -- %s" % str(e)[:160]
        return empty

def orchestration_fields():
    """Snapshot last loop/monitor evidence. Cite #213. Not slogan-only."""
    empty = {
        "loop_ok": False, "loop_copy": "", "loop_when": "", "loop_model": "",
        "loop_steps": 0, "loop_hid": "", "loop_status": "", "loop_evidence": "",
        "loop_next": "Attach OpenCode | Hermes | Grok | Codex | Claude",
    }
    mod, err = _load_orchestration_213()
    if mod is None:
        empty["loop_copy"] = "FAIL orchestration -- module missing"
        empty["loop_next"] = "./pfy setup"
        return empty
    try:
        return mod.snapshot_fields(STATE)
    except Exception as e:
        empty["loop_copy"] = "FAIL orchestration -- %s" % str(e)[:160]
        return empty

def code_graph_fields():
    """Snapshot live code-graph path (axon vs codebase-memory). Cite #215."""
    empty = {
        "graph_ok": False, "graph_copy": "", "graph_when": "", "graph_path": "",
        "graph_bin": "", "graph_evidence": "", "graph_next": "pip install axoniq · ./pfy catalog ask axon",
    }
    mod, err = _load_code_graph_215()
    if mod is None:
        empty["graph_copy"] = "FAIL code-graph -- module missing"
        empty["graph_next"] = "./pfy setup"
        return empty
    try:
        return mod.snapshot_fields(STATE)
    except Exception as e:
        empty["graph_copy"] = "FAIL code-graph -- %s" % str(e)[:160]
        return empty

def catalog_fields(active=""):
    """Snapshot catalog browse + live queue status. Cite #214. Never dump scores-only."""
    empty = {
        "catalog_ok": False, "catalog": [], "catalog_copy": "",
        "catalog_next": "pick a catalog tool on Tools", "catalog_queue": [],
        "catalog_pending": {}, "catalog_busy": False, "catalog_prompt": "",
        "catalog_attached": "", "catalog_hold": "catalog 70-75 HOLD (do not auto-lift)",
    }
    live, _lerr = _load_live_org_214()
    if live is not None:
        try:
            return live.snapshot_fields(STATE, ROOT, active=active or "", pid_alive=pid_alive)
        except Exception as e:
            empty["catalog_copy"] = "FAIL catalog -- %s" % str(e)[:160]
            return empty
    mod, err = _load_catalog_209()
    if mod is None:
        empty["catalog_copy"] = "FAIL catalog -- module missing"
        empty["catalog_next"] = "./pfy setup"
        return empty
    try:
        return mod.snapshot_fields(STATE, ROOT, active=active or "", pid_alive=pid_alive)
    except Exception as e:
        empty["catalog_copy"] = "FAIL catalog -- %s" % str(e)[:160]
        return empty

def _session_reach_live():
    oc, hm, gk, cx, cl = "", "", "", "", ""
    mod, err = _load_enterable_162()
    if mod is not None:
        try:
            if hasattr(mod, "live_session_reach"):
                oc = mod.live_session_reach(STATE, pid_alive) or ""
            else:
                oc = mod.read_session_reach(STATE) or ""
        except Exception:
            oc = ""
    hmod, _herr = _load_attach_196()
    if hmod is not None:
        try:
            if hasattr(hmod, "live_session_reach"):
                hm = hmod.live_session_reach(STATE, pid_alive) or ""
        except Exception:
            hm = ""
    gmod, _gerr = _load_attach_202()
    if gmod is not None:
        try:
            if hasattr(gmod, "live_session_reach"):
                gk = gmod.live_session_reach(STATE, pid_alive) or ""
        except Exception:
            gk = ""
    cmod, _cerr = _load_attach_220()
    if cmod is not None:
        try:
            if hasattr(cmod, "live_session_reach"):
                cx = cmod.live_session_reach(STATE, pid_alive) or ""
        except Exception:
            cx = ""
    clmod, _clerr = _load_attach_221()
    if clmod is not None:
        try:
            if hasattr(clmod, "live_session_reach"):
                cl = clmod.live_session_reach(STATE, pid_alive) or ""
        except Exception:
            cl = ""
    try:
        cur = active_harness("grok")
    except Exception:
        cur = ""
    if cur in ("claude", "claude-code") and cl:
        return cl
    if cur == "codex" and cx:
        return cx
    if cur == "grok" and gk:
        return gk
    if cur == "hermes" and hm:
        return hm
    if cur == "opencode" and oc:
        return oc
    return cl or cx or gk or hm or oc or ""

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


def open_enterable_hermes_session():
    """Attach Hermes + prove models list + smoke. Cite #196."""
    mod, err = _load_attach_196()
    stub = hermes_stub_line()
    if mod is None:
        return {
            "ok": False, "id": "hermes", "live": "FAIL", "copy": stub,
            "error": err or "hermes attach module missing", "session_reach": "FAIL",
            "usable": False,
        }
    def _set_active(hid):
        (STATE / "active-harness").write_text(str(hid) + "\n", encoding="utf-8")
    return mod.open_enterable_hermes_session(
        ROOT=ROOT, STATE=STATE, which_bin=which_bin,
        live_openai_base=live_openai_base, inspect_models=inspect_models,
        record_sidecar_pid=record_sidecar_pid, record_last_verb=record_last_verb,
        pid_alive=pid_alive, active_harness_setter=_set_active, stub_line=stub,
    )


def open_enterable_grok_session():
    """Attach Grok + prove models list + smoke. Cite #202."""
    mod, err = _load_attach_202()
    stub = grok_stub_line()
    if mod is None:
        return {
            "ok": False, "id": "grok", "live": "FAIL", "copy": stub,
            "error": err or "grok attach module missing", "session_reach": "FAIL",
            "usable": False,
        }
    def _set_active(hid):
        (STATE / "active-harness").write_text(str(hid) + "\n", encoding="utf-8")
    return mod.open_enterable_grok_session(
        ROOT=ROOT, STATE=STATE, which_bin=which_bin,
        live_openai_base=live_openai_base, inspect_models=inspect_models,
        record_sidecar_pid=record_sidecar_pid, record_last_verb=record_last_verb,
        pid_alive=pid_alive, active_harness_setter=_set_active, stub_line=stub,
    )


def open_enterable_codex_session():
    """Attach Codex + prove models list + smoke. Cite #220."""
    mod, err = _load_attach_220()
    stub = codex_stub_line()
    if mod is None:
        return {
            "ok": False, "id": "codex", "live": "FAIL", "copy": stub,
            "error": err or "codex attach module missing", "session_reach": "FAIL",
            "usable": False,
        }
    def _set_active(hid):
        (STATE / "active-harness").write_text(str(hid) + "\n", encoding="utf-8")
    return mod.open_enterable_codex_session(
        ROOT=ROOT, STATE=STATE, which_bin=which_bin,
        live_openai_base=live_openai_base, inspect_models=inspect_models,
        record_sidecar_pid=record_sidecar_pid, record_last_verb=record_last_verb,
        pid_alive=pid_alive, active_harness_setter=_set_active, stub_line=stub,
    )


def open_enterable_claude_session():
    """Attach Claude + prove models list + smoke. Cite #221."""
    mod, err = _load_attach_221()
    stub = claude_stub_line()
    if mod is None:
        return {
            "ok": False, "id": "claude", "live": "FAIL", "copy": stub,
            "error": err or "claude attach module missing", "session_reach": "FAIL",
            "usable": False,
        }
    def _set_active(hid):
        (STATE / "active-harness").write_text(str(hid) + "\n", encoding="utf-8")
    return mod.open_enterable_claude_session(
        ROOT=ROOT, STATE=STATE, which_bin=which_bin,
        live_openai_base=live_openai_base, inspect_models=inspect_models,
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
    """Fresh FreeToken-first detect at call time (#171). Ready detect base only.

    Do not fall back to shell LOCAL_OPENAI_BASE_URL (often a stale Ollama Launch pin).
    """
    det = detector_json()
    status = str(det.get("status") or "").strip().lower()
    base = str(det.get("base_url") or "").strip()
    if base == "(none)":
        base = ""
    # Ready + non-empty detect base wins — FreeToken before Ollama when both up.
    if status == "ready" and base:
        b = base.rstrip("/")
        if not b.endswith("/v1"):
            b = b + "/v1"
        return b, det
    return "", det


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