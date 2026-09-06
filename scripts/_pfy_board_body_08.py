pid, "log": str(log),
            "role": "monitor",
        }
    record_sidecar_pid("grok", proc.pid)
    record_last_verb("start grok")
    write_monitor_note("monitor pid %s · %s" % (proc.pid, note))
    return {
        "ok": True, "id": "grok", "live": "READY", "pid": proc.pid,
        "sidecar": True, "log": str(log), "role": "monitor",
        "note": last_monitor_note(),
    }

SKILL_IDS = ("one-shot", "investigate", "agent-loops", "hermes-feedback")
SKILLS_ROOT = ROOT / "bootstrap" / "grok-cli" / "skills"
TOOLS_FILE = STATE / "tools.json"
MCP_FRAGMENT = ROOT / "bootstrap" / "grok-cli" / "config" / "config.fragment.toml"
WRITE_GUARD_DIR = ROOT / "harness" / "write-guard-mcp"
WRITE_GUARD_ALT = ROOT / "tools" / "write-guard-mcp"
TOOLS_ENV = ROOT / "examples" / "opencode-ollama" / ".generated" / "tools-model.env"
MERGE_PY = ROOT / "bootstrap" / "grok-cli" / "scripts" / "merge_config.py"
WG_OVERLAY = ROOT / "harness" / "agent-cage" / "overlays" / "write-guard" / "mcp-servers.write-guard.yaml"
OPENCODE_JSON = STATE / "opencode.json"
STATE_GROK = STATE / "grok-config.toml"

def default_tools_state():
    skills = {}
    for sid in SKILL_IDS:
        skills[sid] = (SKILLS_ROOT / sid / "SKILL.md").is_file()
    return {
        "skills": skills,
        "mcp": False,
        "write_guard": False,
        "tools_mode": "split",
    }

def load_tools_state():
    base = default_tools_state()
    if TOOLS_FILE.is_file():
        try:
            raw = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw = {}
        if isinstance(raw, dict):
            sk = raw.get("skills") if isinstance(raw.get("skills"), dict) else {}
            for sid in SKILL_IDS:
                if sid in sk:
                    base["skills"][sid] = bool(sk[sid])
            if "mcp" in raw:
                base["mcp"] = bool(raw.get("mcp"))
            if "write_guard" in raw:
                base["write_guard"] = bool(raw.get("write_guard"))
            mode = str(raw.get("tools_mode") or "").strip()
            if mode in ("split", "local_tools"):
                base["tools_mode"] = mode
    return base

def save_tools_state(st):
    STATE.mkdir(parents=True, exist_ok=True)
    TOOLS_FILE.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")

def apply_skills_dir(st):
    dest = STATE / "opencode-skills"
    dest.mkdir(parents=True, exist_ok=True)
    for child in list(dest.iterdir()):
        try:
            child.unlink()
        except OSError:
            pass
    enabled = []
    for sid in SKILL_IDS:
        if not st.get("skills", {}).get(sid):
            continue
        src = SKILLS_ROOT / sid
        if not (src / "SKILL.md").is_file():
            continue
        link = dest / sid
        try:
            link.symlink_to(src)
        except OSError:
            return None, "cannot link " + sid
        enabled.append(sid)
    return dest, enabled

def local_tools_model():
    name = (os.environ.get("LOCAL_TOOLS_MODEL") or "").strip()
    if name:
        return name
    if TOOLS_ENV.is_file():
        for line in TOOLS_ENV.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s.startswith("export LOCAL_TOOLS_MODEL="):
                return s.split("=", 1)[1].strip().strip("'\"")
            if s.startswith("LOCAL_TOOLS_MODEL="):
                return s.split("=", 1)[1].strip().strip("'\"")
    return ""


def grok_home():
    return Path(os.environ.get("GROK_HOME") or str(Path.home() / ".grok"))

def grok_config_path():
    return grok_home() / "config.toml"

def write_guard_root():
    if WRITE_GUARD_DIR.is_dir():
        return WRITE_GUARD_DIR
    if WRITE_GUARD_ALT.is_dir():
        return WRITE_GUARD_ALT
    return None

def upsert_env_file(path, updates):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if path.is_file():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()