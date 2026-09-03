#!/usr/bin/env python3
"""Local operator board. Independent poller — not a daemon, not a supervisor.

Serves the shared GUI at gui/operator/frontend/index.html.
POST /start spawns OpenCode worker or optional Grok monitor sidecar. local-only never auto-calls cloud.
POST /stage runs ./pfy stage (env-stage).
POST /env runs ./pfy env (inference + env-stage). No harness exec.
POST /models/pull runs ./pfy models pull <name>.
POST /eval runs a live-endpoint chat/completions probe against LOCAL_OPENAI_BASE_URL.
POST /tools toggles skills, MCP, write-guard, extra tools.
"""
from __future__ import annotations
import json, os, shutil, socket, subprocess, sys, urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"
DETECT = ROOT / "scripts" / "detect-local-runtime.sh"
REG = ROOT / "data" / "harnesses.json"
STATE = Path(os.environ.get("PFY_STATE_DIR", str(Path.home() / ".pfy-mentat")))
HOST = os.environ.get("PFY_BOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("PFY_BOARD_PORT", "8765"))
REFRESH_MS = int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000"))
DETECT_ORDER = [
    ("freetoken", "FreeToken", ":1919"),
    ("llama-swap", "llama-swap", ":9292"),
    ("llama.cpp", "llama-server", ":8080"),
    ("ollama", "Ollama", ":11434"),
]
PS_MATCH = {
    "freetoken": ("ft", "freetoken"), "llama-swap": ("llama-swap",),
    "llama.cpp": ("llama-server",), "llama-server": ("llama-server",),
    "ollama": ("ollama",), "shimmy": ("shimmy",), "grok": ("grok",),
    "opencode": ("opencode", "opencode-cli"), "hermes": ("hermes", "hermes-agent"),
    "claude-code": ("claude",), "codex": ("codex",), "gemini": ("gemini", "gemini-cli"),
    "exo": ("exo.sh", "exo"),
}
STUB_ALWAYS = {"continue", "agent-cage"}
NO_SPAWN = {"llama-swap", "llama.cpp", "llama-server", "shimmy"}
SIDECAR_OK = {"grok", "opencode"}
ISSUE_BASE = "https://github.com/themark-net/pfy-mentat/issues/"
GROK_USE = "pfy harness use grok"
FRONTEND = ROOT / "gui" / "operator" / "frontend" / "index.html"
ORG_CANDIDATES = (
    STATE / "org-messages.jsonl", STATE / "org-messages.json",
    ROOT / "data" / "org-messages.jsonl", ROOT / "data" / "org-messages.json",
    ROOT / ".pfy" / "org-messages.jsonl", ROOT / ".pfy" / "org-messages.json",
)
ENGINE_ALIAS = {"ft": "freetoken", "llama-server": "llama.cpp", "freetoken": "freetoken"}
ALLOWED_LIVE = frozenset({"ready", "partial", "stub", "detected-stub", "missing", "skip"})

def honest_live(value):
    v = str(value or "").strip().lower()
    if v in ALLOWED_LIVE:
        return v
    return "missing"

def _run(argv, timeout=20.0):
    try:
        p = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return p.returncode, (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")

def load_registry():
    if not REG.is_file():
        return {"harnesses": [], "default_harness": "grok"}
    return json.loads(REG.read_text(encoding="utf-8"))

def detector_json():
    if not DETECT.is_file():
        return {"engine": "none", "status": "missing", "base_url": ""}
    _rc, out = _run(["bash", str(DETECT), "--json"], timeout=8.0)
    for raw in out.splitlines():
        s = raw.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                d = json.loads(s)
            except json.JSONDecodeError:
                break
            if isinstance(d, dict):
                return {"engine": d.get("engine") or "none", "status": d.get("status") or "missing", "base_url": d.get("base_url") or ""}
    return {"engine": "none", "status": "missing", "base_url": ""}

def pfy_status_stdout():
    rc, out = _run(["bash", str(PFY), "status"], timeout=25.0)
    return out if out.strip() else f"(pfy status empty, exit {rc})"

def parse_status(text):
    active, usage, chips = "", [], []
    runtime = {"engine": "", "status": "", "base_url": ""}
    in_usage = in_table = False
    for line in text.splitlines():
        if line.startswith("active harness:"):
            active = line.split(":", 1)[1].strip(); in_usage = False; continue
        if line.startswith("local runtime:"):
            for part in line.split(":", 1)[1].split():
                if "=" in part:
                    k, v = part.split("=", 1); runtime[k] = v
            in_usage = False; continue
        if line.startswith("usage:"):
            in_usage = True; in_table = False; continue
        stripped = line.strip()
        if stripped.startswith("ID") and "STATUS" in line:
            in_table = True; in_usage = False; continue
        if in_table:
            if stripped.startswith("----") or stripped.startswith("next:") or stripped.startswith("override:"):
                if stripped.startswith("next:") or stripped.startswith("override:"):
                    in_table = False
                continue
            if not stripped:
                in_table = False; continue
            parts = stripped.split(None, 3)
            if len(parts) >= 3:
                chips.append({"id": parts[0], "live": honest_live(parts[1]), "role": parts[2], "name": parts[3] if len(parts) > 3 else ""})
            continue
        if in_usage:
            if not stripped:
                in_usage = False; continue
            usage.append(line.rstrip())
    return {"active": active, "runtime": runtime, "usage": usage, "chips": chips}

def process_table():
    rc, out = _run(["ps", "-eo", "pid,args"], timeout=5.0)
    if rc != 0:
        rc, out = _run(["ps", "ax", "-o", "pid,args"], timeout=5.0)
    rows = []
    for line in out.splitlines()[1:]:
        s = line.strip()
        if not s:
            continue
        pid, _, args = s.partition(" ")
        low = args.lower()
        if "pfy-board.py" in low or "pfy-gui.py" in low or "pfy-operator" in low:
            continue
        hit = ""
        for hid, needles in PS_MATCH.items():
            for n in needles:
                tok = n.lower()
                if tok in low.split() or f"/{tok}" in low or low.endswith(tok):
                    hit = hid; break
            if hit:
                break
        if hit:
            rows.append({"pid": pid, "id": hit, "args": args.strip()[:180]})
    return rows

def last_verb():
    p = STATE / "last-verb"
    if not p.is_file():
        return {"verb": "(none)", "when": ""}
    verb, when = "(none)", ""
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("verb:"):
            verb = line.split(":", 1)[1].strip() or "(none)"
        elif line.startswith("when:"):
            when = line.split(":", 1)[1].strip()
    return {"verb": verb, "when": when}

def active_harness(default):
    p = STATE / "active-harness"
    if p.is_file():
        v = p.read_text(encoding="utf-8", errors="replace").strip()
        if v:
            return v
    return default

def deploy_profile():
    envp = ROOT / ".env"
    if envp.is_file():
        for line in envp.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("DEPLOY_PROFILE="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return os.environ.get("DEPLOY_PROFILE", "")

def inspect_models(base_url):
    if not base_url:
        return []
    base = base_url.rstrip("/")
    ids, seen = [], set()
    for path in ("/v1/models", "/api/tags"):
        try:
            req = urllib.request.Request(base + path, method="GET")
            with urllib.request.urlopen(req, timeout=2) as r:
                d = json.loads(r.read().decode() or "{}")
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for key in ("data", "models"):
            for m in d.get(key) or []:
                name = (m.get("id") or m.get("name") or m.get("model") if isinstance(m, dict) else str(m)) or ""
                name = str(name).strip()
                if name and name not in seen:
                    seen.add(name); ids.append(name)
    return ids

def org_messages():
    for path in ORG_CANDIDATES:
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace").strip()
        if not raw:
            continue
        items = []
        if path.suffix == ".jsonl":
            for line in raw.splitlines():
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        else:
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError:
                continue
            items = loaded if isinstance(loaded, list) else (loaded.get("messages") or loaded.get("items") or [loaded])
        out = []
        for it in items:
            if not isinstance(it, dict):
                continue
            who = str(it.get("from") or it.get("who") or "")
            whom = str(it.get("to") or it.get("whom") or "")
            if who or whom:
                out.append({"from": who, "to": whom, "pr": it.get("pr") or "", "issue": it.get("issue") or "",
                            "state": str(it.get("state") or it.get("status") or ""),
                            "text": str(it.get("text") or it.get("summary") or "")[:240]})
        return out
    return []

def one_liner(hid, rec):
    if hid in STUB_ALWAYS:
        return GROK_USE
    if hid == "llama-swap":
        return "llama-swap"
    if hid in ("llama.cpp", "llama-server"):
        return "llama-server"
    if hid == "shimmy":
        return "shimmy"
    if hid == "freetoken":
        return "ft serve --model $PFY_FT_MODEL"
    if hid == "ollama":
        return "ollama serve"
    if hid == "grok":
        return "curl -fsSL https://x.ai/cli/install.sh | bash"
    setup = str(rec.get("setup") or "").strip()
    return (setup.splitlines()[0] if setup else f"./pfy start {hid}")

def now_state(active, live, procs, verb):
    ids = {r["id"] for r in procs}
    mapped = "llama.cpp" if active == "llama-server" else active
    if mapped in STUB_ALWAYS or live in ("stub", "detected-stub", "missing"):
        return "blocked"
    if mapped in ids or active in ids:
        return "running"
    v = verb.get("verb") or ""
    return "blocked" if v.startswith("start") or v.startswith("up") else "idle"

def rsf_inference(det):
    st = (det.get("status") or "").strip().lower()
    if st == "ready":
        return "READY"
    if st == "partial":
        return "FAIL"
    return "SKIP"

def rsf_env_stage(verb, usage):
    blob = " ".join(usage).lower()
    v = (verb.get("verb") or "").strip()
    if "fail" in blob or "error" in blob:
        return "FAIL"
    if "honest skip" in blob or "skip: env-stage" in blob:
        return "SKIP"
    if v.startswith(("start", "up", "stage", "gui", "board", "env", "launch-env")):
        return "READY"
    return "SKIP"

def rsf_attach(active, live_active):
    if active in STUB_ALWAYS:
        return "FAIL"
    live = (live_active or "").lower()
    if live == "ready":
        return "READY"
    if live in ("stub", "detected-stub"):
        return "FAIL"
    return "SKIP"

def tape_steps(det, verb, usage, active, live_active):
    return [
        {"id": "inference", "label": "inference", "live": rsf_inference(det)},
        {"id": "env-stage", "label": "env-stage", "live": rsf_env_stage(verb, usage)},
        {"id": "harness-attach", "label": "harness attach", "live": rsf_attach(active, live_active)},
    ]
def snapshot():
    reg = load_registry()
    harnesses = list(reg.get("harnesses") or [])
    default = str(reg.get("default_harness") or "grok")
    det = detector_json()
    status_text = pfy_status_stdout()
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



def run_stage():
    """Run product env-stage (./pfy stage). Not --lab. Honest skip is PASS."""
    if not PFY.is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL env-stage", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "stage"], timeout=90.0)
    ok = rc == 0
    live = "PASS" if ok else "FAIL"
    copy = "PASS env-stage" if ok else "FAIL env-stage"
    return {
        "ok": ok, "live": live, "copy": copy,
        "error": "" if ok else ((out or "env-stage failed")[-400:]),
        "stdout": (out or "")[-800:],
    }

def test_model():
    # Live-endpoint eval: OpenAI-compat chat/completions on detector base_url.
    # Same completion path as examples/opencode-ollama/smoke.sh, against LOCAL_OPENAI_BASE_URL.
    # Not eval-integration-change. PASS only if the endpoint returns a completion.
    det = detector_json()
    st = str(det.get("status") or "").strip().lower()
    eng = str(det.get("engine") or "none").strip().lower()
    base = str(det.get("base_url") or os.environ.get("LOCAL_OPENAI_BASE_URL") or "").strip()
    if base == "(none)":
        base = ""
    live = st == "ready" and eng not in ("", "none") and bool(base)
    if not live:
        return {"ok": True, "live": "SKIP", "copy": "SKIP eval", "error": ""}
    models = inspect_models(base)
    name = ""
    if models:
        name = str(models[0]).strip()
    if not name:
        name = (
            os.environ.get("LOCAL_CODER_MODEL")
            or os.environ.get("PFY_FT_MODEL")
            or os.environ.get("PFY_OLLAMA_MODEL")
            or os.environ.get("PFY_LLAMA_MODEL")
            or ""
        ).strip()
    if not name:
        return {"ok": False, "live": "FAIL", "copy": "FAIL eval", "error": "no model on live endpoint"}
    root = base.rstrip("/")
    if root.endswith("/v1"):
        url = root + "/chat/completions"
    else:
        url = root + "/v1/chat/completions"
    payload = json.dumps({
        "model": name,
        "messages": [{"role": "user", "content": "Reply with exactly: PFY_EVAL_OK"}],
        "max_tokens": 32,
        "temperature": 0,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode() or "{}")
    except Exception as e:
        return {"ok": False, "live": "FAIL", "copy": "FAIL eval", "error": str(e)[:400]}
    text = ""
    try:
        choice = (data.get("choices") or [{}])[0]
        if not isinstance(choice, dict):
            choice = {}
        msg = choice.get("message") or {}
        if isinstance(msg, dict):
            text = msg.get("content") or ""
        if not text:
            text = choice.get("text") or ""
    except Exception:
        text = ""
    if len(str(text).strip()) < 2:
        return {"ok": False, "live": "FAIL", "copy": "FAIL eval", "error": "empty completion"}
    return {"ok": True, "live": "PASS", "copy": "PASS eval", "stdout": str(text).strip()[:400]}

def pull_model(name):
    # Live-engine pull: FreeToken records; Ollama pulls; llama skip honest.
    name = (name or "").strip()
    if not name:
        return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "no name"}
    if not PFY.is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL pull", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "models", "pull", name], timeout=180.0)
    blob = (out or "")
    low = blob.lower()
    if rc != 0:
        return {
            "ok": False, "live": "FAIL", "copy": "FAIL pull",
            "error": (blob or "pull failed")[-400:],
            "stdout": blob[-800:],
        }
    if "honest skip" in low or "has no pull" in low or "no local engine" in low:
        return {"ok": True, "live": "SKIP", "copy": "SKIP pull", "stdout": blob[-800:]}
    return {"ok": True, "live": "PASS", "copy": "PASS pull", "stdout": blob[-800:]}

def launch_env():
    """Same path as bare ./pfy before the window: inference then env-stage. No harness exec."""
    if not PFY.is_file():
        return {"ok": False, "live": "FAIL", "copy": "FAIL env", "error": "scripts/pfy missing"}
    rc, out = _run(["bash", str(PFY), "env"], timeout=120.0)
    ok = rc == 0
    copy = "PASS env" if ok else "FAIL env"
    return {
        "ok": ok, "live": "PASS" if ok else "FAIL", "copy": copy,
        "error": "" if ok else ((out or "env failed")[-400:]),
        "stdout": (out or "")[-800:],
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
    path = STATE / "opencode.json"
    path.write_text(json.dumps(cfg, indent=2) + chr(10), encoding="utf-8")
    return path, name

def record_sidecar_pid(hid, pid):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / ("sidecar-%s.pid" % hid)).write_text(str(pid) + chr(10), encoding="utf-8")

def sidecar_pid_live():
    for hid in ("opencode", "grok"):
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
SKILLS_ROOT = ROOT / "bootstrap" / "grok-cli" / "skills"
TOOLS_FILE = STATE / "tools.json"
MCP_FRAGMENT = ROOT / "bootstrap" / "grok-cli" / "config" / "config.fragment.toml"
WRITE_GUARD_DIR = ROOT / "harness" / "write-guard-mcp"
WRITE_GUARD_ALT = ROOT / "tools" / "write-guard-mcp"
TOOLS_ENV = ROOT / "examples" / "opencode-ollama" / ".generated" / "tools-model.env"

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
        if want and not MCP_FRAGMENT.is_file():
            return {"ok": False, "live": "FAIL", "copy": "FAIL mcp", "error": "mcp recipe missing", "id": tid}
        st["mcp"] = want
        save_tools_state(st)
        (STATE / "mcp-on").write_text("1\n" if want else "0\n", encoding="utf-8")
        return {"ok": True, "live": "PASS", "copy": ("ON " if want else "OFF ") + "mcp", "id": tid, "on": want, "tools": st}
    if tid in ("write-guard", "write_guard"):
        if want and not (WRITE_GUARD_DIR.is_dir() or WRITE_GUARD_ALT.is_dir()):
            return {"ok": False, "live": "FAIL", "copy": "FAIL write-guard", "error": "write-guard missing", "id": "write-guard"}
        st["write_guard"] = want
        save_tools_state(st)
        (STATE / "write-guard-mode").write_text(("enforce\n" if want else "off\n"), encoding="utf-8")
        return {"ok": True, "live": "PASS", "copy": ("ON " if want else "OFF ") + "write-guard", "id": "write-guard", "on": want, "tools": st}
    if tid in ("extra-tools", "local_tools", "tools_mode"):
        mode = "local_tools" if want else "split"
        if mode == "local_tools" and not local_tools_model():
            return {"ok": False, "live": "FAIL", "copy": "FAIL extra tools", "error": "no local tools model", "id": "extra-tools"}
        st["tools_mode"] = mode
        save_tools_state(st)
        STATE.mkdir(parents=True, exist_ok=True)
        (STATE / "tools-mode").write_text(mode + "\n", encoding="utf-8")
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
        (STATE / "active-harness").write_text("opencode\n", encoding="utf-8")
        record_last_verb("start opencode")
        return {
            "ok": True, "id": hid, "live": "READY", "pid": proc.pid,
            "sidecar": True, "log": str(log), "base_url": base, "model": model,
        }
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

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[pfy] " + (fmt % args) + "\n")
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, html_page().encode("utf-8"), "text/html; charset=utf-8"); return
        if path == "/snapshot":
            self._send(200, json.dumps(snapshot(), indent=2).encode("utf-8"), "application/json; charset=utf-8"); return
        self._send(404, b"not found\n", "text/plain; charset=utf-8")
    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/start":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            hid = str((body or {}).get("id") or "")
            result = start_sidecar(hid)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/stage":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = run_stage()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/env":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = launch_env()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/models/pull":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            name = str((body or {}).get("name") or "")
            result = pull_model(name)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/eval":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            result = test_model()
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        if path == "/tools":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                body = {}
            tid = str((body or {}).get("id") or "")
            on = (body or {}).get("on")
            result = set_tool(tid, on)
            code = 200 if result.get("ok") else 400
            self._send(code, json.dumps(result).encode("utf-8"), "application/json; charset=utf-8")
            return
        self._send(405, b"POST disabled for this path\n", "text/plain; charset=utf-8")

def main():
    args = sys.argv[1:]
    if args[:1] == ["--snapshot"]:
        print(json.dumps(snapshot()))
        return 0
    if args[:1] == ["--start"]:
        hid = args[1] if len(args) > 1 else ""
        result = start_sidecar(hid)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--stage"]:
        result = run_stage()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--env"]:
        result = launch_env()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--pull"]:
        name = args[1] if len(args) > 1 else ""
        result = pull_model(name)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--eval"]:
        result = test_model()
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if args[:1] == ["--tool"]:
        tid = args[1] if len(args) > 1 else ""
        onraw = args[2] if len(args) > 2 else "1"
        on = str(onraw).strip().lower() in ("1", "true", "on", "yes")
        result = set_tool(tid, on)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    if HOST not in ("127.0.0.1", "localhost"):
        print("error: operator HTTP binds loopback only", file=sys.stderr); return 2
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print("native window")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
