#!/usr/bin/env python3
"""Local operator board. Independent poller — not a daemon, not a supervisor.

Serves the shared GUI at gui/operator/frontend/index.html.
POST /start spawns grok/opencode as a sidecar subprocess only.
POST /stage runs ./pfy stage (env-stage).
"""
from __future__ import annotations
import json, os, socket, subprocess, sys, urllib.request
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
    if v.startswith(("start", "up", "stage", "gui", "board")):
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

def start_sidecar(hid):
    """Spawn grok/opencode as a separate process. Not a supervisor for other ids."""
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
