#!/usr/bin/env python3
"""Native operator window. Tauri is preferred by scripts/pfy.

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

def ensure_http(board):
    host = getattr(board, "HOST", os.environ.get("PFY_BOARD_HOST", "127.0.0.1"))
    port = int(getattr(board, "PORT", os.environ.get("PFY_BOARD_PORT", "8765")))
    httpd = None
    if not port_open(host, port):
        from http.server import ThreadingHTTPServer
        httpd = ThreadingHTTPServer((host, port), board.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://{host}:{port}/"

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
        view = WebKit2.WebView(); view.load_uri(url); win.add(view); win.show_all()
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
        self.busy = False; self.msg = ""; self.view = "loop"; self.snap = {}
        tk = sys.modules["tkinter"]; ttk = sys.modules["tkinter.ttk"]
        root.title("pfy"); root.geometry("1280x800"); root.configure(bg=BG); root.minsize(960, 640)
        st = ttk.Style()
        try: st.theme_use("clam")
        except tk.TclError: pass
        st.configure("TFrame", background=BG); st.configure("TLabel", background=BG, foreground=FG)
        st.configure("M.TLabel", background=BG, foreground=MUTED)
        st.configure("H.TLabel", background=BG, foreground=FG, font=("sans-serif", 13, "bold"))
        st.configure("F.TLabel", background=BG, foreground="#e8875b", font=("sans-serif", 11, "bold"))
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
        self.banner = ttk.Label(right, text="", style="M.TLabel", wraplength=1040, justify="left")
        self.banner.pack(anchor="w", padx=12)
        split = ttk.Frame(right); split.pack(fill="x", padx=12, pady=4)
        self.lfr = tk.Frame(split, bg=PANE); self.lfr.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(self.lfr, text="LOCAL WORKER", bg=PANE, fg=FG, font=("sans-serif", 12, "bold")).pack(anchor="w", padx=8, pady=(8,2))
        self.local = tk.Label(self.lfr, text="", bg=PANE, fg=FG, justify="left", wraplength=500, anchor="w")
        self.local.pack(anchor="w", padx=8, pady=(0,8))
        cfr = tk.Frame(split, bg=CLOUD); cfr.pack(side="left", fill="both", expand=True, padx=(4, 0))
        tk.Label(cfr, text="CLOUD MONITOR", bg=CLOUD, fg=FG, font=("sans-serif", 12, "bold")).pack(anchor="w", padx=8, pady=(8,2))
        self.cloud = tk.Label(cfr, text="", bg=CLOUD, fg=FG, justify="left", wraplength=500, anchor="w")
        self.cloud.pack(anchor="w", padx=8, pady=(0,8))
        self.tape = ttk.Label(right, text="", justify="left"); self.tape.pack(anchor="w", padx=12)
        btns = ttk.Frame(right); btns.pack(fill="x", padx=12, pady=6)
        self.bgrok = ttk.Button(btns, text="Attach grok", command=lambda: self.attach("grok")); self.bgrok.pack(side="left", padx=(0,6))
        self.bopen = ttk.Button(btns, text="Attach opencode", command=lambda: self.attach("opencode")); self.bopen.pack(side="left")
        self.ast = ttk.Label(btns, text="", style="M.TLabel"); self.ast.pack(side="left", padx=12)
        self.fail = ttk.Label(right, text="", style="F.TLabel"); self.fail.pack(anchor="w", padx=12)
        self.body = ttk.Label(right, text="", justify="left", wraplength=1040); self.body.pack(anchor="w", padx=12, pady=6)
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
            pid = res.get("pid"); self.msg = f"sidecar {hid}" + (f" pid {pid}" if pid else "")
        else:
            self.msg = "FAIL " + (res.get("copy") or GROK_USE)
        self.ast.configure(text=self.msg); self.refresh()

    def refresh(self):
        if self.busy or self.board is None: return
        self.busy = True
        def work():
            try: snap = self.board.snapshot()
            except Exception as e: snap = {"error": str(e)}
            self.root.after(0, lambda: self.apply(snap))
        threading.Thread(target=work, daemon=True).start()

    def apply(self, s):
        self.busy = False; self.snap = s or {}; self.render()

    def render(self):
        tk = sys.modules["tkinter"]; s = self.snap
        if s.get("error") and not s.get("chips"):
            self.meta.configure(text=str(s.get("error"))); return
        self.meta.configure(text=f"{s.get('ts') or ''} · {s.get('host') or ''} · profile {s.get('profile') or '(unset)'}")
        hon = s.get("honest") or {}
        notes = []
        if hon.get("note_nimo"):
            notes.append(hon["note_nimo"])
        self.banner.configure(text="\n".join(notes))
        d, r = s.get("detector") or {}, s.get("status_runtime") or {}
        eng_live = honest(s.get("engine_live") or d.get("status"))
        engine = d.get("engine") or r.get("engine") or "none"
        url = d.get("base_url") or r.get("base_url") or "(none)"
        usage = "\n".join(s.get("usage") or []) or "(empty)"
        bg = "#1a3d2f" if eng_live == "ready" else PANE
        self.lfr.configure(bg=bg)
        for c in self.lfr.winfo_children():
            try: c.configure(bg=bg)
            except tk.TclError: pass
        self.local.configure(text=f"engine {engine}  {eng_live}\nstatus {honest(d.get('status'))}\nURL {url}\n{usage}")
        chips = s.get("chips") or []
        grok = next((c for c in chips if c.get("id")=="grok"), {}) or {}
        self.cloud.configure(text=f"grok PATH {honest(grok.get('live'))}\nrole monitor / DoD")
        tape = s.get("tape") or []
        bits = [f"{i}. {t.get('label') or t.get('id')} {t.get('live') or 'SKIP'}" for i,t in enumerate(tape,1)]
        self.tape.configure(text=" then ".join(bits) if bits else "1. inference SKIP then 2. env-stage SKIP then 3. harness attach SKIP")
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
        now = s.get("now") or "idle"
        stage = next((t for t in tape if t.get("id")=="env-stage"), {}) or {}
        if self.view == "loop":
            txt = f"LOOP\nattached   {attached}\nlast       {verb}\ntape       {' then '.join(bits)}\nnow        window owns the process; sidecar is a button · state {now}"
            if stub: txt += f"\nFAIL       {s.get('blocked_copy') or GROK_USE}"
        elif self.view == "engine":
            order = "\n".join(("> " if o.get("winner") else "  ") + f"{o.get('label')} {o.get('port')} · {honest(o.get('live'))}" for o in (s.get("detect_order") or []))
            txt = f"ENGINE\nengine     {engine}\nlive       {eng_live}\nURL        {url}\nusage      {usage}\n{order}"
        elif self.view == "stage":
            sl = stage.get("live") or "SKIP"
            txt = f"STAGE\nenv-stage   {sl}\n" + ("skip is honest (never painted as failure of the env)\n" if sl=="SKIP" else "") + "what ran    scripts/env-stage.sh (or skip reason)"
        elif self.view == "attach":
            txt = f"ATTACH\nrail    every harness.json id · live chip from ./pfy status\nNOW     attached {attached} · last {verb} · state {now}"
            if stub: txt += f"\nFAIL    {s.get('blocked_copy') or GROK_USE}"
        else:
            rows = s.get("org_messages") or []
            txt = "no org loop" if not rows else "ORG\n" + "\n".join(f"{m.get('from')} → {m.get('to')}  {m.get('state') or ''}" for m in rows)
        if self.msg: txt += "\n" + self.msg
        self.body.configure(text=txt)
        for c in self.chips.winfo_children(): c.destroy()
        if self.view in ("attach", "loop"):
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
        title = root.title(); root.destroy()
        return title == "pfy"
    w.poll(int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000"))); root.mainloop(); return True

def main() -> int:
    if os.environ.get("PFY_GUI_SELFTEST")=="1" or "--selftest" in sys.argv:
        return 0 if run_tk(None, True) else 1
    try: board = load_board()
    except Exception as e:
        print(f"error: native window could not open: {e}", file=sys.stderr); return 1
    httpd, url = ensure_http(board)
    try:
        if run_webkit(url): return 0
        if run_tk(board, False): return 0
        if os.environ.get("PFY_GUI_DEV")=="1" and run_pywebview(url): return 0
        print("error: native window could not open", file=sys.stderr); return 1
    finally:
        if httpd is not None:
            try: httpd.shutdown()
            except Exception: pass

if __name__ == "__main__":
    raise SystemExit(main())
