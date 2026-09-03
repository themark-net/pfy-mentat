#!/usr/bin/env python3
"""Native operator window. scripts/pfy prefers a current Tauri binary; else this file.

Order here: WebKit2 (gi) → stdlib tk. pywebview only if PFY_GUI_DEV=1 and it imports.
Print native window (webkit) or native window (tk). Never STUB. Never exit 2.
"""
from __future__ import annotations
import importlib.util, os, socket, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ("ready", "partial", "stub", "detected-stub", "missing", "skip")
GROK_USE = "pfy harness use grok"
BLOCKED = frozenset({"continue", "agent-cage"})
FG, BG, SIDE, PANE, CLOUD, MUTED = "#e8edf4", "#0e1116", "#121821", "#151a22", "#1a2740", "#8b97a8"
CHIP = {"ready":"#3dd68c","partial":"#e6c15a","stub":"#e8875b","detected-stub":"#c984f0","missing":"#7d8796","skip":"#7d8796"}

def honest(v):
    s = (v or "").strip().lower()
    return s if s in LIVE else "missing"

def stopped_exit(error):
    state = Path(os.environ.get("PFY_STATE_DIR", str(Path.home() / ".pfy-mentat")))
    state.mkdir(parents=True, exist_ok=True)
    artifact = state / "gui-stopped-exit.txt"
    artifact.write_text(f"STOPPED_EXIT\nerror: {error}\n", encoding="utf-8")
    print(f"STOPPED_EXIT: {error}", file=sys.stderr)
    print(f"artifact: {artifact}", file=sys.stderr)
    return 1

def load_board():
    path = ROOT / "scripts" / "pfy-board.py"
    spec = importlib.util.spec_from_file_location("pfy_board", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def port_open(host, port):
    s = socket.socket(); s.settimeout(0.3)
    try:
        s.connect((host, port)); return True
    except OSError:
        return False
    finally:
        s.close()

def leftover_dump(body, hdr=""):
    """True when HTML is the old consultant board, not the current session."""
    h = (hdr or "").strip().lower()
    b = body or ""
    low = b.lower()
    if h == "session" and 'data-pfy-ui="session"' in b and "pfy board" not in low:
        return False
    if "pfy board" in low or "start via cli" in low:
        return True
    if "127.0.0.1:8765" in b and "<title>pfy</title>" not in low:
        return True
    return False

def occupant_html(host, port):
    import urllib.request
    try:
        req = urllib.request.Request(f"http://{host}:{port}/", method="GET")
        with urllib.request.urlopen(req, timeout=0.4) as r:
            hdr = (r.headers.get("X-Pfy-UI") or "")
            body = r.read(16000).decode("utf-8", "replace")
        return hdr, body
    except Exception:
        return "", ""

def bind_http(board, host, port):
    from http.server import ThreadingHTTPServer
    httpd = ThreadingHTTPServer((host, port), board.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

def ensure_http(board):
    """Serve current frontend. Never reuse a leftover listener just because the port answered."""
    host = getattr(board, "HOST", os.environ.get("PFY_BOARD_HOST", "127.0.0.1"))
    preferred = int(getattr(board, "PORT", os.environ.get("PFY_BOARD_PORT", "8765")))
    if host not in ("127.0.0.1", "localhost"):
        host = "127.0.0.1"
    from http.server import ThreadingHTTPServer
    httpd = None
    chosen = None
    tried = [preferred] + [p for p in range(preferred + 1, preferred + 16)]
    for port in tried:
        if port_open(host, port):
            continue
        try:
            httpd = bind_http(board, host, port)
            chosen = port
            break
        except OSError:
            continue
    if httpd is None:
        httpd = ThreadingHTTPServer((host, 0), board.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        chosen = httpd.server_address[1]
    return httpd, f"http://{host}:{chosen}/"

def run_webkit(url) -> bool:
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        ok = False
        for ver in ("4.1", "4.0"):
            try:
                gi.require_version("WebKit2", ver); ok = True; break
            except ValueError:
                continue
        if not ok:
            return False
        from gi.repository import Gtk, WebKit2
        win = Gtk.Window(title="pfy"); win.set_default_size(1280, 800)
        win.connect("destroy", Gtk.main_quit)
        view = WebKit2.WebView()
        try:
            stg = view.get_settings()
            stg.set_enable_javascript(True)
            stg.set_javascript_can_access_clipboard(True)
        except Exception:
            pass
        view.load_uri(url); win.add(view); win.show_all()
    except Exception:
        return False
    print("native window (webkit)", flush=True)
    Gtk.main()
    return True

def run_pywebview(url) -> bool:
    try:
        import webview
        webview.create_window("pfy", url, width=1280, height=800)
    except Exception:
        return False
    print("native window (pywebview)", flush=True)
    webview.start()
    return True

class Win:
    def __init__(self, board, root):
        self.board, self.root = board, root
        self.busy = False; self.msg = ""; self.view = "loop"; self.snap = {}; self.pending_user = False
        tk = sys.modules["tkinter"]; ttk = sys.modules["tkinter.ttk"]
        root.title("pfy"); root.geometry("1280x800"); root.configure(bg=BG); root.minsize(960, 640)
        st = ttk.Style()
        try: st.theme_use("clam")
        except tk.TclError: pass
        st.configure("TFrame", background=BG); st.configure("TLabel", background=BG, foreground=FG)
        st.configure("M.TLabel", background=BG, foreground=MUTED)
        st.configure("H.TLabel", background=BG, foreground=FG, font=("sans-serif", 13, "bold"))
        st.configure("F.TLabel", background=BG, foreground="#e8875b", font=("sans-serif", 11, "bold"))
        st.configure("Ok.TLabel", background=BG, foreground="#3dd68c", font=("sans-serif", 11, "bold"))
        outer = ttk.Frame(root); outer.pack(fill="both", expand=True)
        side = tk.Frame(outer, bg=SIDE, width=168); side.pack(side="left", fill="y"); side.pack_propagate(False)
        tk.Label(side, text="pfy", bg=SIDE, fg=FG, font=("sans-serif", 16, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        self.nav = {}
        for k, lab in (("loop","Loop"),("engine","Engine"),("stage","Stage"),("attach","Attach"),("org","Org")):
            b = tk.Button(side, text=lab, bg=SIDE, fg=FG, bd=0, highlightthickness=0, anchor="w", padx=14, pady=8,
                          command=lambda x=k: self.set_view(x))
            b.pack(fill="x"); self.nav[k] = b
        self.nav["org"].pack_forget()
        right = ttk.Frame(outer); right.pack(side="left", fill="both", expand=True)
        head = ttk.Frame(right); head.pack(fill="x", padx=12, pady=(8, 2))
        ttk.Label(head, text="pfy", style="H.TLabel").pack(side="left")
        self.meta = ttk.Label(head, text="polling…", style="M.TLabel"); self.meta.pack(side="left", padx=12)
        self.fail = ttk.Label(right, text="", style="F.TLabel"); self.fail.pack(anchor="w", padx=12, pady=(4,0))
        self.body = ttk.Label(right, text="", justify="left", wraplength=1040); self.body.pack(anchor="w", padx=12, pady=8)
        self.acts = ttk.Frame(right); self.acts.pack(fill="x", padx=12, pady=6)
        self.bgrok = ttk.Button(self.acts, text="Attach grok", command=lambda: self.attach("grok"))
        self.bopen = ttk.Button(self.acts, text="Attach opencode", command=lambda: self.attach("opencode"))
        self.brefresh = ttk.Button(self.acts, text="Refresh status", command=self.refresh_now)
        self.bcopy = ttk.Button(self.acts, text="Copy stub one-liner", command=self.copy_stub)
        self.bstage = ttk.Button(self.acts, text="Run stage", command=self.run_stage)
        self.benv = ttk.Button(self.acts, text="Launch env", command=self.launch_env)
        self.bpull = ttk.Button(self.acts, text="Pull", command=self.pull_model)
        self.btest = ttk.Button(self.acts, text="Test model", command=self.test_model)
        self.pullname = ttk.Entry(self.acts, width=22)
        self.sst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.est = ttk.Label(self.acts, text="", style="M.TLabel")
        self.pst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.tst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.ast = ttk.Label(self.acts, text="", style="Ok.TLabel")
        self.cst = ttk.Label(self.acts, text="", style="M.TLabel")
        self.chips = ttk.Frame(right); self.chips.pack(fill="both", expand=True, padx=12, pady=(0,10))

    def set_view(self, k):
        self.view = k; self.render()

    def attach(self, hid):
        def work():
            try: snap = self.board.snapshot() if self.board else {}
            except Exception as e: snap, err = {}, str(e)
            else: err = ""
            active = str(snap.get("active") or "")
            if active in BLOCKED:
                res = {"ok": False, "copy": GROK_USE, "error": f"{active} is active — no grok/opencode fallback"}
            else:
                try: res = self.board.start_sidecar(hid)
                except Exception as e: res = {"ok": False, "copy": GROK_USE, "error": str(e) or err}
            self.root.after(0, lambda: self.done(hid, res))
        threading.Thread(target=work, daemon=True).start()

    def done(self, hid, res):
        if res.get("ok"):
            pid = res.get("pid")
            kind = "monitor" if res.get("role") == "monitor" else hid
            self.msg = f"attached {kind}" + (f" pid {pid}" if pid else "")
            self.ast.configure(text=self.msg, style="Ok.TLabel")
        else:
            self.msg = "FAIL  " + (res.get("copy") or GROK_USE)
            self.ast.configure(text=self.msg, style="F.TLabel")
        self.refresh()

    def paint_copy(self, text, fail=False):
        self.cst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def stub_line(self):
        s = self.snap or {}
        if s.get("active_stub") or str(s.get("active") or "") in BLOCKED:
            return s.get("blocked_copy") or GROK_USE
        chips = s.get("chips") or []
        active_id = s.get("active")
        active = next((c for c in chips if c.get("id") == active_id), None)
        stubish = ("stub", "detected-stub", "missing")
        def is_stubish(c):
            return honest(c.get("live")) in stubish
        c = active if active and is_stubish(active) else next(
            (x for x in chips if is_stubish(x) and (x.get("one_liner") or x.get("startable") is False)),
            None,
        )
        if not c:
            return ""
        return c.get("one_liner") or ("./pfy start " + str(c.get("id") or ""))

    def copy_stub(self):
        line = self.stub_line()
        if not line:
            self.paint_copy("FAIL no stub one-liner", True)
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(line)
            try:
                self.root.update_idletasks()
            except Exception:
                pass
            self.paint_copy("copied", False)
        except Exception:
            self.paint_copy("FAIL clipboard", True)

    def paint_stage(self, text, fail=False):
        self.sst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def paint_eval(self, text, fail=False):
        self.tst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def test_model(self):
        self.paint_eval("testing…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.btest.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL eval", "error": "no board"}
                else:
                    res = self.board.test_model()
            except Exception as e:
                res = {"ok": False, "copy": "FAIL eval", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_eval(r))
        threading.Thread(target=work, daemon=True).start()

    def done_eval(self, res):
        try:
            self.btest.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            copy = res.get("copy") or "PASS eval"
            if str(copy).startswith("SKIP"):
                self.tst.configure(text=copy, style="M.TLabel")
            elif str(copy).startswith("FAIL"):
                self.paint_eval(copy, True)
            else:
                self.paint_eval(copy, False)
        else:
            self.paint_eval("FAIL " + (res.get("copy") or res.get("error") or "eval"), True)
        self.refresh(user=True)

    def paint_pull(self, text, fail=False):
        self.pst.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def pull_model(self):
        try:
            name = (self.pullname.get() or "").strip()
        except Exception:
            name = ""
        if not name:
            self.paint_pull("FAIL pull", True)
            return
        self.paint_pull("pulling…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.bpull.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL pull", "error": "no board"}
                else:
                    res = self.board.pull_model(name)
            except Exception as e:
                res = {"ok": False, "copy": "FAIL pull", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_pull(r))
        threading.Thread(target=work, daemon=True).start()

    def done_pull(self, res):
        try:
            self.bpull.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            copy = res.get("copy") or "PASS pull"
            self.paint_pull(copy, False)
        else:
            self.paint_pull("FAIL " + (res.get("copy") or res.get("error") or "pull"), True)
        self.refresh(user=True)

    def paint_env(self, text, fail=False):
        self.est.configure(text=text, style="F.TLabel" if fail else "Ok.TLabel")

    def launch_env(self):
        self.paint_env("launching env…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.benv.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL env", "error": "no board"}
                else:
                    res = self.board.launch_env()
            except Exception as e:
                res = {"ok": False, "copy": "FAIL env", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_env(r))
        threading.Thread(target=work, daemon=True).start()

    def done_env(self, res):
        try:
            self.benv.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            self.paint_env(res.get("copy") or "PASS env", False)
        else:
            self.paint_env("FAIL " + (res.get("copy") or res.get("error") or "env"), True)
        self.refresh(user=True)

    def run_stage(self):
        self.paint_stage("running env-stage…", False)
        self.meta.configure(text="refreshing…")
        try:
            self.bstage.configure(state="disabled")
        except Exception:
            pass
        def work():
            try:
                if self.board is None:
                    res = {"ok": False, "copy": "FAIL env-stage", "error": "no board"}
                else:
                    res = self.board.run_stage()
            except Exception as e:
                res = {"ok": False, "copy": "FAIL env-stage", "error": str(e)}
            self.root.after(0, lambda r=res: self.done_stage(r))
        threading.Thread(target=work, daemon=True).start()

    def done_stage(self, res):
        try:
            self.bstage.configure(state="normal")
        except Exception:
            pass
        if res.get("ok"):
            self.paint_stage(res.get("copy") or "PASS env-stage", False)
        else:
            self.paint_stage("FAIL " + (res.get("copy") or res.get("error") or "env-stage"), True)
        self.refresh(user=True)

    def refresh_now(self):
        self.refresh(user=True)

    def refresh(self, user=False):
        if self.board is None:
            if user:
                self.meta.configure(text="FAIL refresh")
                self.fail.configure(text="FAIL  " + GROK_USE)
            return
        if self.busy:
            if user:
                self.pending_user = True
                self.meta.configure(text="refreshing…")
                try:
                    self.brefresh.configure(state="disabled")
                except Exception:
                    pass
            return
        self.busy = True
        if user:
            self.meta.configure(text="refreshing…")
            try:
                self.brefresh.configure(state="disabled")
            except Exception:
                pass
        def work():
            try:
                snap = self.board.snapshot()
            except Exception as e:
                snap = {"error": str(e)}
            self.root.after(0, lambda s=snap, u=user: self.apply(s, user=u))
        threading.Thread(target=work, daemon=True).start()

    def apply(self, s, user=False):
        pending = self.pending_user
        self.pending_user = False
        self.busy = False
        try:
            self.brefresh.configure(state="normal")
        except Exception:
            pass
        self.snap = s or {}
        self.render()
        if user:
            ts = self.snap.get("ts") or ""
            if not ts and not self.snap.get("error"):
                cur = str(self.meta.cget("text") or "")
                if "refreshed" not in cur:
                    self.meta.configure(text=(cur + " · refreshed").strip(" ·"))
        if pending:
            self.refresh(user=True)

    def pack_acts(self, names):
        for w in (self.bgrok, self.bopen, self.brefresh, self.bcopy, self.bstage, self.benv, self.bpull, self.btest, self.pullname, self.sst, self.est, self.pst, self.tst, self.ast, self.cst):
            try: w.pack_forget()
            except Exception: pass
        order = {
            "grok": self.bgrok, "open": self.bopen, "refresh": self.brefresh,
            "copy": self.bcopy, "stage": self.bstage, "env": self.benv,
            "pull": self.bpull, "pullname": self.pullname, "pst": self.pst,
            "test": self.btest, "tst": self.tst,
            "sst": self.sst, "est": self.est, "ast": self.ast, "cst": self.cst,
        }
        for n in names:
            w = order[n]
            w.pack(side="left", padx=(0, 8))

    def render(self):
        tk = sys.modules["tkinter"]; s = self.snap
        if s.get("error") and not s.get("chips"):
            self.meta.configure(text=str(s.get("error"))); return
        self.meta.configure(text=" · ".join(x for x in (s.get("host") or "", s.get("profile") or "", s.get("ts") or "") if x))
        d, r = s.get("detector") or {}, s.get("status_runtime") or {}
        eng_live = honest(s.get("engine_live") or d.get("status"))
        engine = d.get("engine") or r.get("engine") or "none"
        chips = s.get("chips") or []
        grok = next((c for c in chips if c.get("id")=="grok"), {}) or {}
        tape = s.get("tape") or []
        stub = bool(s.get("active_stub")) or str(s.get("active") or "") in BLOCKED
        self.bgrok.configure(state="disabled" if stub else "normal")
        self.bopen.configure(state="disabled" if stub else "normal")
        self.fail.configure(text=(f"FAIL  {s.get('blocked_copy') or GROK_USE}") if stub else "")
        show_org = (not s.get("agent_lane_collapsed", True)) and bool(s.get("org_messages"))
        if show_org: self.nav["org"].pack(fill="x")
        else:
            self.nav["org"].pack_forget()
            if self.view == "org": self.view = "loop"
        for k,b in self.nav.items():
            b.configure(bg="#243041" if k==self.view else SIDE)
        attached = s.get("active") or "(none)"; verb = (s.get("last_verb") or {}).get("verb") or "(none)"
        if verb in ("env", "launch-env"):
            verb = "Launch env"
        when = (s.get("last_verb") or {}).get("when") or ""
        pid = s.get("sidecar_pid") or ""
        att = attached + (f" pid {pid}" if pid else "")
        stage = next((t for t in tape if t.get("id")=="env-stage"), {}) or {}
        inf = next((t for t in tape if t.get("id")=="inference"), {}) or {}
        lives = [str(inf.get("live") or "SKIP").upper(), str(stage.get("live") or "SKIP").upper()]
        if "FAIL" in lives:
            env_live = "FAIL"
        elif "READY" in lives:
            env_live = "READY"
        else:
            env_live = "SKIP"
        if self.view == "loop":
            note = s.get("monitor_note") or ""
            mpid = s.get("monitor_pid") or ""
            mon = note or (f"pid {mpid}" if mpid else "(none)")
            gpath = s.get("grok_path") or honest(grok.get("live"))
            txt = f"LOOP\nenv        {env_live}\nattached   {att}\nlast       {verb}  {when}\nmonitor    {mon}\ngrok       {gpath}"
            if stub: txt += f"\nFAIL       {s.get('blocked_copy') or GROK_USE}"
            if self.msg: txt += "\n" + self.msg
            self.pack_acts(["env", "open", "grok", "est", "ast"])
        elif self.view == "engine":
            models = s.get("models") or []
            mtxt = " · ".join(str(x) for x in models) if models else "(none)"
            txt = f"ENGINE\nengine     {engine}\nlive       {eng_live}\ngrok       {honest(grok.get('live'))}\nmodels     {mtxt}"
            self.pack_acts(["refresh", "test", "pullname", "pull", "tst", "pst"])
        elif self.view == "stage":
            sl = stage.get("live") or "SKIP"
            txt = f"STAGE\nenv-stage   {sl}"
            self.pack_acts(["stage", "sst"])
        elif self.view == "attach":
            txt = f"ATTACH\nNOW     attached {attached} · last {verb}"
            if stub: txt += f"\nFAIL    {s.get('blocked_copy') or GROK_USE}"
            self.pack_acts(["grok", "open", "copy", "cst"])
        else:
            rows = s.get("org_messages") or []
            txt = "no org loop" if not rows else "ORG\n" + "\n".join(f"{m.get('from')} → {m.get('to')}  {m.get('state') or ''}" for m in rows)
            self.pack_acts([])
        self.body.configure(text=txt)
        for c in self.chips.winfo_children(): c.destroy()
        if self.view == "attach":
            for c in chips:
                hid, live, role, name = c.get("id") or "", honest(c.get("live")), c.get("role") or "", c.get("name") or ""
                fr = tk.Frame(self.chips, bg="#18202c", highlightbackground="#243041", highlightthickness=1, padx=8, pady=6)
                fr.pack(side="left", padx=4, pady=4, anchor="n")
                tk.Label(fr, text=hid, bg="#18202c", fg=FG, font=("sans-serif", 10, "bold")).pack(anchor="w")
                tk.Label(fr, text=live, bg="#18202c", fg=CHIP.get(live, CHIP["missing"]), font=("sans-serif", 9, "bold")).pack(anchor="w")
                tk.Label(fr, text=f"{role} · {name}", bg="#18202c", fg=MUTED).pack(anchor="w")
                if hid in BLOCKED:
                    tk.Label(fr, text=GROK_USE, bg="#111823", fg=FG, font=("monospace", 9)).pack(anchor="w", pady=(4,0))

    def poll(self, ms=2000):
        self.refresh()
        def tick():
            self.refresh(); self.root.after(ms, tick)
        self.root.after(ms, tick)

def selftest_snap():
    return {"ts":"selftest","host":"selftest","profile":"","detector":{"engine":"none","status":"missing","base_url":""},
            "engine_live":"missing","usage":[],"chips":[{"id":"grok","live":"missing","role":"harness","name":"Grok CLI"},
            {"id":"continue","live":"stub","role":"harness","name":"Continue"}],
            "tape":[{"id":"inference","label":"inference","live":"SKIP"},{"id":"env-stage","label":"env-stage","live":"SKIP"},
                    {"id":"harness-attach","label":"harness attach","live":"SKIP"}],
            "detect_order":[],"active":"grok","active_stub":False,"blocked_copy":GROK_USE,
            "last_verb":{"verb":"gui","when":""},"now":"idle","processes":[],"agent_lane_collapsed":True}

def selftest_fresh_bind():
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import urlparse
    import urllib.request
    class Dump(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            b = b"<!DOCTYPE html><html><head><title>pfy board</title></head><body>127.0.0.1:8765 start via CLI nimo honest-state</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
    class Ours(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            b = b'<!DOCTYPE html><html data-pfy-ui="session"><head><title>pfy</title></head><body>LOOP Attach grok</body></html>'
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("X-Pfy-UI", "session")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
    dump = ThreadingHTTPServer(("127.0.0.1", 0), Dump)
    threading.Thread(target=dump.serve_forever, daemon=True).start()
    dport = dump.server_address[1]
    class Board:
        HOST = "127.0.0.1"
        PORT = dport
        Handler = Ours
    httpd, url = ensure_http(Board)
    try:
        got = urlparse(url).port
        if got == dport:
            return False
        with urllib.request.urlopen(url, timeout=1) as r:
            body = r.read().decode("utf-8", "replace")
            hdr = (r.headers.get("X-Pfy-UI") or "")
        return (
            not leftover_dump(body, hdr)
            and "pfy board" not in body.lower()
            and "start via cli" not in body.lower()
            and "<title>pfy</title>" in body
        )
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        try:
            dump.shutdown()
        except Exception:
            pass

def run_tk(board, selftest=False) -> bool:
    try:
        import tkinter as tk; import tkinter.ttk  # noqa
        root = tk.Tk()
    except Exception:
        return False
    print("native window (tk)", flush=True)
    w = Win(board, root)
    if selftest:
        w.apply(selftest_snap()); root.update_idletasks(); root.update()
        title = root.title()
        has = (
            w.bgrok.cget("text") == "Attach grok"
            and w.bopen.cget("text") == "Attach opencode"
            and w.brefresh.cget("text") == "Refresh status"
            and w.bcopy.cget("text") == "Copy stub one-liner"
            and w.bstage.cget("text") == "Run stage"
            and w.benv.cget("text") == "Launch env"
            and w.bpull.cget("text") == "Pull"
            and w.btest.cget("text") == "Test model"
        )
        w.set_view("loop")
        body = w.body.cget("text") or ""
        loop_ok = "LOOP" in body and "env" in body.lower() and "LOCAL WORKER" not in body and "pfy board" not in body.lower()
        w.copy_stub()
        copied = (w.cst.cget("text") == "copied")
        try:
            clip = root.clipboard_get()
        except Exception:
            clip = ""
        root.destroy()
        return title == "pfy" and has and loop_ok and copied and bool(clip)
    w.poll(int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000"))); root.mainloop(); return True

def main() -> int:
    if os.environ.get("PFY_GUI_SELFTEST")=="1" or "--selftest" in sys.argv:
        return 0 if run_tk(None, True) and selftest_fresh_bind() else 1
    try: board = load_board()
    except Exception as e:
        return stopped_exit(str(e))
    httpd, url = ensure_http(board)
    try:
        if run_webkit(url): return 0
        if run_tk(board, False): return 0
        if os.environ.get("PFY_GUI_DEV")=="1" and run_pywebview(url): return 0
        return stopped_exit("no already-on-box toolkit opened a native window")
    finally:
        if httpd is not None:
            try: httpd.shutdown()
            except Exception: pass

if __name__ == "__main__":
    raise SystemExit(main())
