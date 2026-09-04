n ("opencode", "grok"):
        path = STATE / ("sidecar-%s.pid" % hid)
        if not path.is_file():
            continue
        try:
            pid = int(path.read_text(encoding="utf-8", errors="replace").strip())
        except ValueError:
            continue
        if pid_alive(pid):
            return pid
    return ""

def record_last_verb(verb):
    STATE.mkdir(parents=True, exist_ok=True)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (STATE / "last-verb").write_text("verb: %s\nwhen: %s\n" % (verb, when), encoding="utf-8")

def opencode_stub_line():
    rec = next((h for h in (load_registry().get("harnesses") or []) if h.get("id") == "opencode"), {}) or {}
    return one_liner("opencode", rec)


def grok_stub_line():
    rec = next((h for h in (load_registry().get("harnesses") or []) if h.get("id") == "grok"), {}) or {}
    return one_liner("grok", rec)

def grok_path_live():
    return "ready" if which_bin("grok") else "missing"

def monitor_pid_live():
    path = STATE / "sidecar-grok.pid"
    if not path.is_file():
        return ""
    try:
        pid = int(path.read_text(encoding="utf-8", errors="replace").strip())
    except ValueError:
        return ""
    return pid if pid_alive(pid) else ""

def last_monitor_note():
    paths = (
        STATE / "monitor-note",
        ROOT / "examples" / "opencode-ollama" / ".generated" / "monitor-brief.md",
    )
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        for line in text.splitlines():
            s = line.strip().lstrip("#").strip()
            if not s:
                continue
            if s.lower().startswith("generated"):
                continue
            return s[:240]
    return ""

def write_monitor_note(text):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "monitor-note").write_text((text or "").strip()[:240] + "\n", encoding="utf-8")

def start_monitor_sidecar():
    stub = grok_stub_line()
    profile = deploy_profile()
    if profile == "local-only":
        return {
            "ok": False, "id": "grok", "live": "FAIL", "copy": "local-only",
            "error": "local-only never auto-calls cloud", "role": "monitor",
        }
    bin_path = which_bin("grok")
    if not bin_path:
        return {
            "ok": False, "id": "grok", "live": "FAIL", "copy": stub,
            "error": "grok missing", "role": "monitor",
        }
    brief = ROOT / "examples" / "opencode-ollama" / ".generated" / "monitor-brief.md"
    note = last_monitor_note()
    if not note:
        note = "review / hard DoD"
        if brief.is_file():
            note = last_monitor_note() or note
    log = STATE / "sidecar-grok.log"
    env = os.environ.copy()
    if brief.is_file():
        env["PFY_MONITOR_BRIEF"] = str(brief)
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
            err = "grok exited"
        return {
            "ok": False, "id": "grok", "live": "FAIL", "copy": stub,
            "error": err or "grok exited", "pid": proc.pid, "log": str(log),
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
SKILLS_ROOT = ROOT / "bootstrap" / "grok