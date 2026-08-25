#!/usr/bin/env python3
"""Local operator board. Independent poller — not a daemon, not a supervisor."""
from __future__ import annotations
import json, os, socket, subprocess, sys, urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"
DETECT = ROOT / "scripts" / "detect-local-runtime.sh"
REG = ROOT / "data" / "harnesses.json"
STATE = Path(os.environ.get("PFY_STATE_DIR", str(Path.home() / ".pfy-mentat")))
HOST = os.environ.get("PFY_BOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("PFY_BOARD_PORT", "3847"))
REFRESH_MS = int(os.environ.get("PFY_BOARD_REFRESH_MS", "4000"))
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
ISSUE_BASE = "https://github.com/themark-net/pfy-mentat/issues/"
GROK_USE = "pfy harness use grok"
ORG_CANDIDATES = (
    STATE / "org-messages.jsonl", STATE / "org-messages.json",
    ROOT / "data" / "org-messages.jsonl", ROOT / "data" / "org-messages.json",
    ROOT / ".pfy" / "org-messages.jsonl", ROOT / ".pfy" / "org-messages.json",
)

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
                chips.append({"id": parts[0], "live": parts[1], "role": parts[2], "name": parts[3] if len(parts) > 3 else ""})
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
        if "pfy-board.py" in low:
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
        live = (parsed_chips.get(hid) or {}).get("live") or "skip"
        issue = h.get("github_issue")
        rec = {
            "id": hid, "name": h.get("name") or hid, "role": h.get("role") or "",
            "live": live, "issue_url": f"{ISSUE_BASE}{issue}" if issue not in (None, "") else "",
            "one_liner": one_liner(hid, h),
            "startable": live == "ready" and hid not in STUB_ALWAYS and hid not in NO_SPAWN,
        }
        if hid in STUB_ALWAYS:
            rec["startable"] = False
            rec["one_liner"] = GROK_USE
        chips.append(rec)
    procs = process_table()
    verb = last_verb()
    active = parsed.get("active") or active_harness(default)
    live_active = next((c["live"] for c in chips if c["id"] == active), "")
    host = socket.gethostname()
    profile = deploy_profile()
    base = det.get("base_url") or (parsed.get("runtime") or {}).get("base_url") or ""
    if base == "(none)":
        base = ""
    eng = det.get("engine") or ""
    alias = {"ft": "freetoken", "llama-server": "llama.cpp"}
    eng_norm = alias.get(eng, eng)
    ready_h = any(c["role"] == "harness" and c["live"] == "ready" for c in chips)
    modes = []
    if det.get("status") == "ready" and ready_h:
        modes.append("all-local-ready")
    if eng_norm == "ollama" or "nimo" in host.lower():
        modes.append("ollama-adapter-only")
    if not ready_h:
        modes.append("missing-harness-or-stub")
    order = []
    for hid, label, port in DETECT_ORDER:
        live = next((c["live"] for c in chips if c["id"] == hid), "missing")
        order.append({"id": hid, "label": label, "port": port, "live": live, "winner": eng_norm == hid,
                      "one_liner": one_liner(hid, next((h for h in harnesses if h.get("id") == hid), {}))})
    msgs = org_messages()
    return {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": host, "root": str(ROOT), "profile": profile, "local_only": profile == "local-only",
        "detector": det, "status_runtime": parsed.get("runtime") or {}, "usage": parsed.get("usage") or [],
        "chips": chips, "active": active, "last_verb": verb, "now": now_state(active, live_active, procs, verb),
        "processes": procs, "detect_order": order, "models": inspect_models(base) if base else [],
        "models_note": "inspect-only — tag list is not success",
        "org_messages": msgs, "agent_lane_collapsed": not msgs,
        "honest": {"modes": modes, "note_nimo": "nimo is an Actions runner with Ollama :11434, not a pfy profile. Empty ollama ps is OK. Ollama is an adapter, not the product."},
        "grok_chip_note": "Grok chip is PATH-only. Auth is attach-time only. No auth column. Grok usage omitted.",
        "midline": "local = bulk · Grok = DoD", "tape": ["inference", "env-stage", "harness attach"],
        "blocked_copy": GROK_USE, "status_stdout": status_text, "no_daemon": True,
    }

def html_page():
    return (
        "<!DOCTYPE html><html lang=en><head><meta charset=utf-8/><title>pfy board</title>"
        "<style>body{margin:0;font:14px/1.4 ui-sans-serif,system-ui,sans-serif;background:#0e1116;color:#e8edf4}"
        "header,.pane,.rail,.now,.order,.models,.agent,.notes,.tape,.banner{padding:12px 18px;border-bottom:1px solid #243041}"
        ".split{display:grid;grid-template-columns:1fr 8px 1fr}.local{background:#1a3d2f}.cloud{background:#1a2740}"
        ".mid{background:#2a3344;writing-mode:vertical-rl;transform:rotate(180deg);display:flex;align-items:center;justify-content:center;font-size:11px}"
        ".chips{display:flex;flex-wrap:wrap;gap:8px}.chip{background:#18202c;border:1px solid #243041;border-radius:10px;padding:8px 10px;min-width:140px}"
        ".ready{color:#3dd68c}.partial{color:#e6c15a}.stub{color:#e8875b}.detected-stub{color:#c984f0}.missing{color:#7d8796}.skip{color:#6aa7d9}"
        ".copy{font-family:ui-monospace,monospace;font-size:12px;background:#111823;padding:4px 6px;border-radius:6px;display:block;margin-top:6px;user-select:all}"
        "button{background:#243041;color:#e8edf4;border:1px solid #243041;border-radius:8px;padding:6px 10px}button:disabled{opacity:.4}"
        ".muted{color:#8b97a8}.banner{background:#3a2a12;color:#f3d9a4}.live{font-weight:700;text-transform:uppercase;font-size:11px}"
        "</style></head><body>"
        "<header><b>pfy board</b> <span class=muted id=meta>polling...</span> <span class=muted>127.0.0.1 · no daemon · chips = status live column</span></header>"
        "<div class=banner id=banners></div><div class=split>"
        "<section class='pane local'><h2>LOCAL WORKER</h2><div id=local></div></section>"
        "<div class=mid id=mid>local = bulk · Grok = DoD</div>"
        "<section class='pane cloud'><h2>CLOUD MONITOR</h2><div id=cloud></div></section></div>"
        "<div class=tape id=tape></div>"
        "<section class=rail><h2>Honesty rail</h2><p class=muted>Live chips from <code>./pfy status</code>. json status ignored.</p><div class=chips id=chips></div></section>"
        "<section class=now id=now></section><section class=order id=order></section>"
        "<details class=models open><summary>Models drawer (inspect-only — tag list is not success)</summary><div id=models></div></details>"
        "<section class=agent id=agent></section><section class=notes id=notes></section>"
        "<script>const REFRESH=" + str(REFRESH_MS) + ";"
        "function cls(s){return (s||'').replace(/[^a-z-]/g,'');}"
        "async function tick(){"
        "const s=await (await fetch('/snapshot',{cache:'no-store'})).json();"
        "document.getElementById('meta').textContent=s.ts+' · '+s.host+' · profile '+(s.profile||'(unset)');"
        "const b=[]; if(s.local_only) b.push('DEPLOY_PROFILE=local-only — never auto-calls cloud. Grok usage omitted.');"
        "b.push(s.honest.note_nimo); (s.honest.modes||[]).forEach(m=>b.push('honest state: '+m));"
        "document.getElementById('banners').innerHTML=b.map(x=>'<div>'+x+'</div>').join('');"
        "const d=s.detector||{}, r=s.status_runtime||{};"
        "document.getElementById('local').innerHTML='engine <b>'+(d.engine||r.engine||'none')+'</b><br>status <b>'+(d.status||r.status||'missing')+'</b><br>URL <code>'+(d.base_url||r.base_url||'(none)')+'</code><pre>'+((s.usage||[]).join('\\n')||'(empty)')+'</pre><p class=muted>Ollama is an adapter, not the product. Board does not spawn llama-swap / llama-server / shimmy.</p>';"
        "const g=(s.chips||[]).find(c=>c.id==='grok')||{};"
        "document.getElementById('cloud').innerHTML='grok chip (PATH-only): <span class=\"live '+cls(g.live)+'\">'+(g.live||'missing')+'</span><p>DoD: Grok reviews / sets exit card. Local does bulk.</p><p class=muted>'+s.grok_chip_note+'</p>';"
        "document.getElementById('mid').textContent=s.midline;"
        "document.getElementById('tape').innerHTML=(s.tape||[]).map((t,i)=>'<span class=chip>'+(i+1)+'. '+t+'</span>').join(' ');"
        "document.getElementById('chips').innerHTML=(s.chips||[]).map(c=>{"
        "const issue=c.issue_url?'<a href=\"'+c.issue_url+'\">issue</a>':'';"
        "const copy='<code class=copy>'+(c.startable?('./pfy start '+c.id):c.one_liner)+'</code>';"
        "const btn=c.startable?'<button data-start=\"'+c.id+'\">start</button>':'<button disabled>start disabled</button>';"
        "return '<div class=chip><b>'+c.id+'</b> <span class=\"live '+cls(c.live)+'\">'+c.live+'</span><div class=muted>'+c.role+' · '+c.name+' '+issue+'</div>'+copy+btn+'</div>';"
        "}).join('');"
        "document.getElementById('now').innerHTML='<h2>Now</h2>attached <b>'+s.active+'</b><br>last verb <b>'+(s.last_verb.verb||'(none)')+'</b> <span class=muted>'+(s.last_verb.when||'')+'</span><br>state <b>'+s.now+'</b> (blocked or running)<br><span class=muted>ps: '+(((s.processes||[]).map(p=>p.id+'#'+p.pid).join(', '))||'(none)')+'</span>';"
        "document.getElementById('order').innerHTML='<h2>Detect order</h2>'+(s.detect_order||[]).map(o=>'<div>'+(o.winner?'> ':'')+o.label+' '+o.port+' · <span class=\"live '+cls(o.live)+'\">'+o.live+'</span>'+(o.live==='partial'?' <code class=copy>'+o.one_liner+'</code>':'')+'</div>').join('');"
        "const tags=(s.models&&s.models.length)?s.models.map(m=>'<li>'+m+'</li>').join(''):'<li>(none — live endpoint not listing or not up)</li>';"
        "document.getElementById('models').innerHTML='<p class=muted>'+s.models_note+'</p><ul>'+tags+'</ul>';"
        "if(s.agent_lane_collapsed){document.getElementById('agent').innerHTML='<h2>Agent lane</h2><p class=muted>collapsed (no org messages). Seats: CEO → PM → DevBot + Reviewer.</p>';}"
        "else {const rows=(s.org_messages||[]).map(m=>'<tr><td>'+m.from+' → '+m.to+'</td><td>'+(m.pr||m.issue||'')+'</td><td>'+(m.state||'')+'</td></tr>').join('');"
        "document.getElementById('agent').innerHTML='<h2>Agent lane</h2><p class=muted>CEO → PM → DevBot + Reviewer</p><table>'+rows+'</table>';}"
        "document.getElementById('notes').innerHTML='<p class=muted>No pfy daemon. Board polls detector JSON + status stdout + ps. Start execs harness. Continue is never detected-stub. Docker on PATH is cage detected-stub, not startable. Continue/agent-cage: STUB exit 2, copy <code>'+s.blocked_copy+'</code>.</p>';"
        "document.querySelectorAll('button[data-start]').forEach(b=>{b.onclick=async()=>{await fetch('/start?id='+encodeURIComponent(b.getAttribute('data-start')),{method:'POST'});};});"
        "} tick(); setInterval(tick, REFRESH);</script></body></html>"
    )

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[pfy-board] " + (fmt % args) + "\n")
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
        parsed = urlparse(self.path)
        if parsed.path != "/start":
            self._send(404, b"not found\n", "text/plain; charset=utf-8"); return
        hid = (parse_qs(parsed.query).get("id") or [""])[0].strip()
        if hid in STUB_ALWAYS or not hid:
            self._send(400, json.dumps({"ok": False, "stub": True, "exit": 2, "copy": GROK_USE, "id": hid or "(none)"}).encode(), "application/json; charset=utf-8"); return
        if hid in NO_SPAWN:
            self._send(400, json.dumps({"ok": False, "copy": one_liner(hid, {}), "note": "board does not spawn this engine"}).encode(), "application/json; charset=utf-8"); return
        subprocess.Popen(["bash", str(PFY), "start", hid], cwd=str(ROOT), start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._send(200, json.dumps({"ok": True, "exec": f"./pfy start {hid}"}).encode(), "application/json; charset=utf-8")

def main():
    if HOST not in ("127.0.0.1", "localhost"):
        print("error: pfy board binds 127.0.0.1 only", file=sys.stderr); return 2
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print("pfy board (local operator GUI)")
    print(f"  http://{HOST}:{PORT}/")
    print("  polls detector JSON + ./pfy status stdout + process table")
    print("  no daemon · not a supervisor · chips == status live column")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nboard stopped")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
