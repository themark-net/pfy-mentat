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
    if h == "session" and ('data-pfy-ui="session"' in b or "data-pfy-ui=session" in b) and "pfy board" not in low:
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
        for k, lab in (("loop","Loop"),("engine","Engine"),("stage","Stage"),("attach","Attach"),("tools","Tools"),("org","Org")):
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
        self.tool_btns = {}
        for tid, lab in (("one-shot","one-shot"),("investigate","investigate"),("agent-loops","agent-loops"),("hermes-feedback","hermes-feedback"),("mcp","mcp"),("write-guard","write-guard"),("extra-tools","extra tools")):
            self.tool_btns[tid] = ttk.Button(self.acts, text=lab, command=lambda x=tid: self.toggle_tool(x))
        self.toolst = ttk.Label(self.acts, text="", style="M.TLabel")
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
