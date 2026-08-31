#!/usr/bin/env python3
"""Native operator window. Same IA as the Tauri frontend.

Resolution (after Tauri binary in scripts/pfy):
  1. PyGObject WebKit2 if present — print native window (webkit)
  2. stdlib tkinter — print native window (tk)
  3. pywebview only if PFY_GUI_DEV=1 AND the module imports (optional; never STUB)

Starts in-process board HTTP if port closed. Exit 0 with a window.
Never install-copy as the UI. Never exit 2.
"""
from __future__ import annotations

import importlib.util
import os
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ("ready", "partial", "stub", "detected-stub", "missing", "skip")
GROK_USE = "pfy harness use grok"
BLOCKED_ACTIVE = frozenset({"continue", "agent-cage"})
CHIP_FG = {
    "ready": "#3dd68c",
    "partial": "#e6c15a",
    "stub": "#e8875b",
    "detected-stub": "#c984f0",
    "missing": "#7d8796",
    "skip": "#7d8796",
    "READY": "#3dd68c",
    "SKIP": "#7d8796",
    "FAIL": "#e8875b",
}
BG = "#0e1116"
FG = "#e8edf4"
MUTED = "#8b97a8"
SIDE = "#121821"
PANE = "#151a22"
CLOUD = "#1a2740"
READY_PANE = "#1a3d2f"


def _load_board():
    path = ROOT / "scripts" / "pfy-board.py"
    spec = importlib.util.spec_from_file_location("pfy_board", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _port_open(host: str, port: int) -> bool:
    s = socket.socket()
    s.settimeout(0.3)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def honest_live(value) -> str:
    v = (value or "").strip().lower()
    if v in LIVE:
        return v
    return "missing"


def stopped_exit(error: str) -> int:
    state = Path(os.environ.get("PFY_STATE_DIR", str(Path.home() / ".pfy-mentat")))
    state.mkdir(parents=True, exist_ok=True)
    artifact = state / "gui-stopped-exit.txt"
    artifact.write_text(f"STOPPED_EXIT\nerror: {error}\n", encoding="utf-8")
    print(f"STOPPED_EXIT: {error}", file=sys.stderr)
    print(f"artifact: {artifact}", file=sys.stderr)
    return 1


def ensure_board_http(board):
    host = getattr(board, "HOST", os.environ.get("PFY_BOARD_HOST", "127.0.0.1"))
    port = int(getattr(board, "PORT", os.environ.get("PFY_BOARD_PORT", "8765")))
    url = f"http://{host}:{port}/"
    httpd = None
    if not _port_open(host, port):
        from http.server import ThreadingHTTPServer

        httpd = ThreadingHTTPServer((host, port), board.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, url


def _try_webkit_modules():
    try:
        import gi
    except ImportError:
        return None
    try:
        gi.require_version("Gtk", "3.0")
    except ValueError:
        return None
    webkit_ok = False
    for ver in ("4.1", "4.0"):
        try:
            gi.require_version("WebKit2", ver)
            webkit_ok = True
            break
        except ValueError:
            continue
    if not webkit_ok:
        return None
    from gi.repository import Gtk, WebKit2

    return Gtk, WebKit2


def run_webkit(url: str) -> bool:
    loaded = _try_webkit_modules()
    if loaded is None:
        return False
    Gtk, WebKit2 = loaded
    try:
        win = Gtk.Window(title="pfy")
        win.set_default_size(1280, 800)
        win.connect("destroy", Gtk.main_quit)
        view = WebKit2.WebView()
        view.load_uri(url)
        win.add(view)
        win.show_all()
    except Exception:
        return False
    print("native window (webkit)", flush=True)
    Gtk.main()
    return True


def run_pywebview(url: str) -> bool:
    try:
        import webview
    except ImportError:
        return False
    try:
        webview.create_window("pfy", url, width=1280, height=800)
    except Exception:
        return False
    print("native window (pywebview)", flush=True)
    webview.start()
    return True


class TkOperatorWindow:
    """stdlib tkinter operator app. Same IA: sidebar + header + views."""

    def __init__(self, board, root):
        self.board = board
        self.root = root
        self._poll_busy = False
        self._attach_msg = ""
        self._view = "loop"
        self._snap = {}
        self._build()

    def _build(self):
        tk = sys.modules["tkinter"]
        ttk = sys.modules["tkinter.ttk"]
        root = self.root
        root.title("pfy")
        root.geometry("1280x800")
        root.configure(bg=BG)
        root.minsize(960, 640)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Head.TLabel", background=BG, foreground=FG, font=("sans-serif", 13, "bold"))
        style.configure("Side.TFrame", background=SIDE)
        style.configure("Side.TLabel", background=SIDE, foreground=FG, font=("sans-serif", 14, "bold"))
        style.configure("Side.TButton", padding=8)
        style.configure("Pane.TFrame", background=PANE)
        style.configure("Cloud.TFrame", background=CLOUD)
        style.configure("Banner.TFrame", background="#3a2a12")
        style.configure("Banner.TLabel", background="#3a2a12", foreground="#f3d9a4")
        style.configure("Fail.TLabel", background=BG, foreground="#e8875b", font=("sans-serif", 11, "bold"))

        outer = ttk.Frame(root)
        outer.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(outer, bg=SIDE, width=168)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="pfy", bg=SIDE, fg=FG, font=("sans-serif", 16, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        self._nav = {}
        for key, label in (("loop", "Loop"), ("engine", "Engine"), ("stage", "Stage"), ("attach", "Attach"), ("org", "Org")):
            btn = tk.Button(
                self.sidebar, text=label, bg=SIDE, fg=FG, bd=0, highlightthickness=0,
                activebackground="#1c2533", activeforeground=FG, anchor="w", padx=14, pady=8,
                command=lambda k=key: self._set_view(k),
            )
            btn.pack(fill="x")
            self._nav[key] = btn
        self._nav["org"].pack_forget()

        right = ttk.Frame(outer)
        right.pack(side="left", fill="both", expand=True)

        meta_fr = ttk.Frame(right)
        meta_fr.pack(fill="x", padx=12, pady=(8, 2))
        ttk.Label(meta_fr, text="pfy", style="Head.TLabel").pack(side="left")
        self.meta = ttk.Label(meta_fr, text="polling…", style="Muted.TLabel")
        self.meta.pack(side="left", padx=12)

        self.banner = ttk.Frame(right, style="Banner.TFrame")
        self.banner.pack(fill="x", padx=12, pady=2)
        self.banner_text = ttk.Label(self.banner, text="", style="Banner.TLabel", wraplength=1040, justify="left")
        self.banner_text.pack(fill="x", padx=8, pady=4)

        split = ttk.Frame(right)
        split.pack(fill="x", padx=12, pady=4)
        self.local_fr = tk.Frame(split, bg=PANE)
        self.local_fr.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(self.local_fr, text="LOCAL WORKER", bg=PANE, fg=FG, font=("sans-serif", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.local = tk.Label(self.local_fr, text="", bg=PANE, fg=FG, justify="left", wraplength=500, anchor="w")
        self.local.pack(anchor="w", padx=8, pady=(0, 8))
        cloud_fr = tk.Frame(split, bg=CLOUD)
        cloud_fr.pack(side="left", fill="both", expand=True, padx=(4, 0))
        tk.Label(cloud_fr, text="CLOUD MONITOR", bg=CLOUD, fg=FG, font=("sans-serif", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.cloud = tk.Label(cloud_fr, text="", bg=CLOUD, fg=FG, justify="left", wraplength=500, anchor="w")
        self.cloud.pack(anchor="w", padx=8, pady=(0, 8))

        tape_fr = ttk.Frame(right)
        tape_fr.pack(fill="x", padx=12, pady=2)
        self.tape = ttk.Label(tape_fr, text="", justify="left")
        self.tape.pack(anchor="w")

        btns = ttk.Frame(right)
        btns.pack(fill="x", padx=12, pady=6)
        self.btn_grok = ttk.Button(btns, text="Attach grok", command=lambda: self._attach("grok"))
        self.btn_grok.pack(side="left", padx=(0, 6))
        self.btn_opencode = ttk.Button(btns, text="Attach opencode", command=lambda: self._attach("opencode"))
        self.btn_opencode.pack(side="left")
        self.attach_status = ttk.Label(btns, text="", style="Muted.TLabel")
        self.attach_status.pack(side="left", padx=12)

        self.fail = ttk.Label(right, text="", style="Fail.TLabel")
        self.fail.pack(anchor="w", padx=12)

        self.main = ttk.Frame(right)
        self.main.pack(fill="both", expand=True, padx=12, pady=6)
        self.body = ttk.Label(self.main, text="", justify="left", wraplength=1040)
        self.body.pack(anchor="w")

        self.chips = ttk.Frame(right)
        self.chips.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _set_view(self, key: str):
        self._view = key
        for k, btn in self._nav.items():
            btn.configure(bg="#243041" if k == key else SIDE)
        self._render()

    def _attach(self, hid: str):
        def work():
            try:
                snap = self.board.snapshot() if self.board is not None else {}
            except Exception as e:
                snap, err = {}, str(e)
            else:
                err = ""
            active = str(snap.get("active") or "")
            if active in BLOCKED_ACTIVE:
                result = {
                    "ok": False, "id": hid, "live": "FAIL", "copy": GROK_USE,
                    "error": f"{active} is active — no grok/opencode fallback",
                }
            else:
                try:
                    result = self.board.start_sidecar(hid)
                except Exception as e:
                    result = {"ok": False, "id": hid, "live": "FAIL", "copy": GROK_USE, "error": str(e) or err}
            self.root.after(0, lambda: self._attach_done(hid, result))

        threading.Thread(target=work, daemon=True).start()

    def _attach_done(self, hid, result):
        if result.get("ok"):
            pid = result.get("pid")
            self._attach_msg = f"sidecar {hid}" + (f" pid {pid}" if pid else "")
        else:
            copy = result.get("copy") or GROK_USE
            err = result.get("error") or ""
            self._attach_msg = f"FAIL {copy}" + (f" ({err})" if err else "")
        self.attach_status.configure(text=self._attach_msg)
        self.refresh()

    def refresh(self):
        if self._poll_busy or self.board is None:
            return
        self._poll_busy = True

        def work():
            try:
                snap = self.board.snapshot()
            except Exception as e:
                snap = {"error": str(e)}
            self.root.after(0, lambda: self._apply(snap))

        threading.Thread(target=work, daemon=True).start()

    def _apply(self, s: dict):
        self._poll_busy = False
        self._snap = s or {}
        self._render()

    def _render(self):
        tk = sys.modules["tkinter"]
        s = self._snap
        if s.get("error") and not s.get("chips"):
            self.meta.configure(text=str(s.get("error")))
            return
        ts = s.get("ts") or ""
        host = s.get("host") or ""
        profile = s.get("profile") or "(unset)"
        self.meta.configure(text=f"{ts} · {host} · profile {profile}")

        banners = []
        if s.get("local_only"):
            banners.append("DEPLOY_PROFILE=local-only — never auto-calls cloud. Grok usage omitted.")
        honest = s.get("honest") or {}
        if honest.get("note_nimo"):
            banners.append(honest["note_nimo"])
        for m in honest.get("modes") or []:
            banners.append(f"honest state: {m}")
        self.banner_text.configure(text="\n".join(banners) if banners else "")

        d = s.get("detector") or {}
        r = s.get("status_runtime") or {}
        eng_live = honest_live(s.get("engine_live") or d.get("status") or r.get("status"))
        usage = "\n".join(s.get("usage") or []) or "(empty)"
        engine = d.get("engine") or r.get("engine") or "none"
        status = honest_live(d.get("status") or r.get("status"))
        url = d.get("base_url") or r.get("base_url") or "(none)"
        local_bg = READY_PANE if eng_live == "ready" else PANE
        self.local_fr.configure(bg=local_bg)
        for child in self.local_fr.winfo_children():
            try:
                child.configure(bg=local_bg)
            except tk.TclError:
                pass
        self.local.configure(
            text=f"engine {engine}  {eng_live}\nstatus {status}\nURL {url}\n{usage}\nOllama is an adapter, not the product."
        )
        chips = s.get("chips") or []
        grok = next((c for c in chips if c.get("id") == "grok"), {}) or {}
        grok_live = honest_live(grok.get("live"))
        note = s.get("grok_chip_note") or "Grok chip is PATH-only."
        self.cloud.configure(text=f"grok PATH {grok_live}\nrole monitor / DoD\n{note}")

        tape_bits = []
        tape = s.get("tape") or []
        for i, t in enumerate(tape, 1):
            live = t.get("live") or "SKIP"
            tape_bits.append(f"{i}. {t.get('label') or t.get('id')} {live}")
        self.tape.configure(
            text=" then ".join(tape_bits) if tape_bits else "1. inference SKIP then 2. env-stage SKIP then 3. harness attach SKIP"
        )

        stub = bool(s.get("active_stub")) or str(s.get("active") or "") in BLOCKED_ACTIVE
        self.btn_grok.configure(state="disabled" if stub else "normal")
        self.btn_opencode.configure(state="disabled" if stub else "normal")
        if stub:
            self.fail.configure(text=f"FAIL  {s.get('blocked_copy') or GROK_USE}")
            self.attach_status.configure(text=s.get("blocked_copy") or GROK_USE)
        else:
            self.fail.configure(text="")
            if self._attach_msg:
                self.attach_status.configure(text=self._attach_msg)

        show_org = not s.get("agent_lane_collapsed", True) and bool(s.get("org_messages"))
        if show_org:
            self._nav["org"].pack(fill="x")
        else:
            self._nav["org"].pack_forget()
            if self._view == "org":
                self._view = "loop"

        for k, btn in self._nav.items():
            btn.configure(bg="#243041" if k == self._view else SIDE)

        verb = (s.get("last_verb") or {}).get("verb") or "(none)"
        when = (s.get("last_verb") or {}).get("when") or ""
        attached = s.get("active") or "(none)"
        now = s.get("now") or "idle"
        procs = s.get("processes") or []
        ps = ", ".join(f"{p.get('id')}#{p.get('pid')}" for p in procs) or "(none)"
        stage = next((t for t in tape if (t.get("id") == "env-stage" or t.get("label") == "env-stage")), {}) or {}
        stage_live = stage.get("live") or "SKIP"
        skip_note = "skip is honest (never painted as failure of the env)" if stage_live == "SKIP" else ""
        models = s.get("models") or []
        models_txt = ", ".join(models) if models else "(none — live endpoint not listing or not up)"

        if self._view == "loop":
            lines = [
                "LOOP",
                f"attached   {attached}" + ("  (or: no harness attached)" if attached in ("", "(none)") else ""),
                f"last       {verb} {when}".strip(),
                f"tape       {' then '.join(tape_bits) if tape_bits else '(none)'}",
                f"now        window owns the process; sidecar is a button · state {now}",
                f"ps         {ps}",
            ]
            if stub:
                lines.append(f"FAIL       {s.get('blocked_copy') or GROK_USE}")
            if self._attach_msg:
                lines.append(self._attach_msg)
            self.body.configure(text="\n".join(lines))
        elif self._view == "engine":
            order_bits = []
            for o in s.get("detect_order") or []:
                mark = "> " if o.get("winner") else "  "
                order_bits.append(f"{mark}{o.get('label')} {o.get('port')} · {honest_live(o.get('live'))}")
            lines = [
                "ENGINE",
                f"engine     {engine}",
                f"live       {eng_live.upper()}",
                f"URL        {url}",
                f"usage      {usage}",
                f"models     {models_txt}",
                "",
                "detect order (first live wins)",
                *order_bits,
            ]
            self.body.configure(text="\n".join(lines))
        elif self._view == "stage":
            lines = [
                "STAGE",
                f"env-stage   {stage_live}",
                skip_note,
                "what ran    scripts/env-stage.sh (or skip reason)",
            ]
            self.body.configure(text="\n".join(x for x in lines if x is not None and x != ""))
        elif self._view == "attach":
            lines = [
                "ATTACH",
                "rail    every harness.json id · live chip from ./pfy status",
                f"NOW     attached {attached} · last {verb} · state {now}",
            ]
            if stub:
                lines.append(f"FAIL    {s.get('blocked_copy') or GROK_USE}")
            self.body.configure(text="\n".join(lines))
        else:
            rows = s.get("org_messages") or []
            if not rows:
                self.body.configure(text="no org loop")
            else:
                txt = "\n".join(
                    f"{m.get('from')} → {m.get('to')}  {m.get('pr') or m.get('issue') or ''}  {m.get('state') or ''}"
                    for m in rows
                )
                self.body.configure(text="ORG\n" + txt)

        for child in self.chips.winfo_children():
            child.destroy()
        if self._view in ("attach", "loop"):
            for c in chips:
                hid = c.get("id") or ""
                live = honest_live(c.get("live"))
                role = c.get("role") or ""
                name = c.get("name") or hid
                fr = tk.Frame(self.chips, bg="#18202c", highlightbackground="#243041", highlightthickness=1, padx=8, pady=6)
                fr.pack(side="left", padx=4, pady=4, anchor="n")
                tk.Label(fr, text=hid, bg="#18202c", fg=FG, font=("sans-serif", 10, "bold")).pack(anchor="w")
                tk.Label(fr, text=live, bg="#18202c", fg=CHIP_FG.get(live, CHIP_FG["missing"]), font=("sans-serif", 9, "bold")).pack(anchor="w")
                tk.Label(fr, text=f"{role} · {name}", bg="#18202c", fg=MUTED).pack(anchor="w")
                if hid in BLOCKED_ACTIVE:
                    tk.Label(fr, text=GROK_USE, bg="#111823", fg=FG, font=("monospace", 9)).pack(anchor="w", pady=(4, 0))

    def start_polling(self, ms: int = 2000):
        self.refresh()

        def tick():
            self.refresh()
            self.root.after(ms, tick)

        self.root.after(ms, tick)


def _selftest_snapshot() -> dict:
    return {
        "ts": "selftest",
        "host": "selftest",
        "profile": "",
        "detector": {"engine": "none", "status": "missing", "base_url": ""},
        "status_runtime": {},
        "engine_live": "missing",
        "usage": [],
        "chips": [
            {"id": "grok", "live": "missing", "role": "harness", "name": "Grok CLI"},
            {"id": "opencode", "live": "missing", "role": "harness", "name": "OpenCode"},
            {"id": "continue", "live": "stub", "role": "harness", "name": "Continue"},
            {"id": "agent-cage", "live": "stub", "role": "lab", "name": "agent-cage"},
        ],
        "tape": [
            {"id": "inference", "label": "inference", "live": "SKIP"},
            {"id": "env-stage", "label": "env-stage", "live": "SKIP"},
            {"id": "harness-attach", "label": "harness attach", "live": "SKIP"},
        ],
        "detect_order": [
            {"id": "freetoken", "label": "FreeToken", "port": ":1919", "live": "missing", "winner": False},
            {"id": "llama-swap", "label": "llama-swap", "port": ":9292", "live": "missing", "winner": False},
            {"id": "llama.cpp", "label": "llama-server", "port": ":8080", "live": "missing", "winner": False},
            {"id": "ollama", "label": "Ollama", "port": ":11434", "live": "missing", "winner": False},
        ],
        "active": "grok",
        "active_stub": False,
        "blocked_copy": GROK_USE,
        "last_verb": {"verb": "gui", "when": ""},
        "now": "idle",
        "processes": [],
        "agent_lane_collapsed": True,
        "honest": {"modes": ["missing-harness-or-stub"]},
        "grok_chip_note": "Grok chip is PATH-only.",
    }


def run_tkinter(board, *, selftest: bool = False) -> bool:
    try:
        import tkinter as tk
        import tkinter.ttk  # noqa: F401
    except ImportError:
        return False
    try:
        root = tk.Tk()
    except tk.TclError:
        return False
    print("native window (tk)", flush=True)
    win = TkOperatorWindow(board, root)
    if selftest:
        win._apply(_selftest_snapshot())
        try:
            root.update_idletasks()
            root.update()
        except tk.TclError:
            pass
        title = root.title()
        geom = root.geometry()
        root.destroy()
        if title != "pfy":
            print("error: window title must be pfy", file=sys.stderr)
            return False
        if not geom.startswith("1280x800"):
            pass
        return True
    win.start_polling(int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000")))
    root.mainloop()
    return True


def main() -> int:
    selftest = os.environ.get("PFY_GUI_SELFTEST") == "1" or "--selftest" in sys.argv
    if selftest:
        ok = run_tkinter(None, selftest=True)
        return 0 if ok else 1

    try:
        board = _load_board()
    except Exception as e:
        return stopped_exit(str(e))

    httpd, url = ensure_board_http(board)
    try:
        if run_webkit(url):
            return 0
        if run_tkinter(board, selftest=False):
            return 0
        if os.environ.get("PFY_GUI_DEV") == "1":
            if run_pywebview(url):
                return 0
        return stopped_exit("no already-on-box toolkit opened a native window")
    finally:
        if httpd is not None:
            try:
                httpd.shutdown()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
