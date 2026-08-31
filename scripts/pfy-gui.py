#!/usr/bin/env python3
"""Native operator window. Same IA as the Tauri frontend.

When pywebview is present, host gui/operator/frontend over the in-process
board HTTP poller. Otherwise open a stdlib tkinter window with live chips
from ./pfy status (engine, env-stage, Attach grok / Attach opencode sidecar,
loop/session). Window always opens. Not Electron. Not Chrome. Not install-tips-as-UI.
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
SIDECAR_OK = ("grok", "opencode")
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


def run_pywebview(board) -> int:
    import webview
    from http.server import ThreadingHTTPServer

    host = getattr(board, "HOST", os.environ.get("PFY_BOARD_HOST", "127.0.0.1"))
    port = int(getattr(board, "PORT", os.environ.get("PFY_BOARD_PORT", "8765")))
    url = f"http://{host}:{port}/"
    httpd = None
    if not _port_open(host, port):
        httpd = ThreadingHTTPServer((host, port), board.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print("native window (pywebview)", flush=True)
    webview.create_window("pfy", url, width=1280, height=900)
    webview.start()
    if httpd is not None:
        httpd.shutdown()
    return 0


def _chip_color(live: str) -> str:
    return CHIP_FG.get(live, CHIP_FG["missing"])


class TkOperatorWindow:
    """stdlib tkinter board. Same IA: engine, env-stage, sidecar attach, loop/session."""

    def __init__(self, board, root):
        self.board = board
        self.root = root
        self._poll_busy = False
        self._attach_msg = ""
        self._build()

    def _build(self):
        tk = sys.modules["tkinter"]
        ttk = sys.modules["tkinter.ttk"]
        root = self.root
        root.title("pfy")
        root.geometry("1280x900")
        root.configure(bg="#0e1116")
        root.minsize(900, 640)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#0e1116")
        style.configure("TLabel", background="#0e1116", foreground="#e8edf4")
        style.configure("Muted.TLabel", background="#0e1116", foreground="#8b97a8")
        style.configure("Head.TLabel", background="#0e1116", foreground="#e8edf4", font=("sans-serif", 14, "bold"))
        style.configure("Pane.TFrame", background="#151a22")
        style.configure("Cloud.TFrame", background="#1a2740")
        style.configure("Banner.TFrame", background="#3a2a12")
        style.configure("Banner.TLabel", background="#3a2a12", foreground="#f3d9a4")
        style.configure("Attach.TButton", padding=6)

        outer = ttk.Frame(root)
        outer.pack(fill="both", expand=True)

        head = ttk.Frame(outer)
        head.pack(fill="x", padx=12, pady=(10, 4))
        ttk.Label(head, text="pfy", style="Head.TLabel").pack(side="left")
        self.meta = ttk.Label(head, text="polling…", style="Muted.TLabel")
        self.meta.pack(side="left", padx=12)
        ttk.Label(head, text="native window · no daemon · chips = status live column", style="Muted.TLabel").pack(side="left")

        self.banner = ttk.Frame(outer, style="Banner.TFrame")
        self.banner.pack(fill="x", padx=12, pady=4)
        self.banner_text = ttk.Label(self.banner, text="", style="Banner.TLabel", wraplength=1200, justify="left")
        self.banner_text.pack(fill="x", padx=8, pady=6)

        split = ttk.Frame(outer)
        split.pack(fill="x", padx=12, pady=4)
        local = ttk.Frame(split, style="Pane.TFrame")
        local.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(local, text="LOCAL WORKER", style="Head.TLabel").pack(anchor="w", padx=8, pady=(8, 2))
        self.local = ttk.Label(local, text="", justify="left", wraplength=560)
        self.local.pack(anchor="w", padx=8, pady=(0, 8))
        cloud = ttk.Frame(split, style="Cloud.TFrame")
        cloud.pack(side="left", fill="both", expand=True, padx=(6, 0))
        ttk.Label(cloud, text="CLOUD MONITOR", style="Head.TLabel").pack(anchor="w", padx=8, pady=(8, 2))
        self.cloud = ttk.Label(cloud, text="", justify="left", wraplength=560)
        self.cloud.pack(anchor="w", padx=8, pady=(0, 8))

        tape_fr = ttk.Frame(outer)
        tape_fr.pack(fill="x", padx=12, pady=4)
        ttk.Label(tape_fr, text="loop / session", style="Head.TLabel").pack(anchor="w")
        self.tape = ttk.Label(tape_fr, text="", justify="left")
        self.tape.pack(anchor="w")

        attach = ttk.Frame(outer)
        attach.pack(fill="x", padx=12, pady=8)
        ttk.Label(attach, text="in-window sidecar attach", style="Head.TLabel").pack(side="left", padx=(0, 12))
        self.btn_grok = ttk.Button(attach, text="Attach grok", style="Attach.TButton", command=lambda: self._attach("grok"))
        self.btn_grok.pack(side="left", padx=4)
        self.btn_opencode = ttk.Button(attach, text="Attach opencode", style="Attach.TButton", command=lambda: self._attach("opencode"))
        self.btn_opencode.pack(side="left", padx=4)
        self.attach_status = ttk.Label(attach, text="", style="Muted.TLabel")
        self.attach_status.pack(side="left", padx=12)

        rail = ttk.Frame(outer)
        rail.pack(fill="both", expand=True, padx=12, pady=4)
        ttk.Label(rail, text="Honesty rail  (live from ./pfy status · missing not unknown)", style="Head.TLabel").pack(anchor="w")
        self.chips = ttk.Frame(rail)
        self.chips.pack(fill="both", expand=True, pady=4)

        now_fr = ttk.Frame(outer)
        now_fr.pack(fill="x", padx=12, pady=4)
        self.now = ttk.Label(now_fr, text="", justify="left", wraplength=1200)
        self.now.pack(anchor="w")

        order_fr = ttk.Frame(outer)
        order_fr.pack(fill="x", padx=12, pady=4)
        ttk.Label(order_fr, text="Detect order", style="Head.TLabel").pack(anchor="w")
        self.order = ttk.Label(order_fr, text="", justify="left")
        self.order.pack(anchor="w")

        agent_fr = ttk.Frame(outer)
        agent_fr.pack(fill="x", padx=12, pady=(4, 10))
        self.agent = ttk.Label(agent_fr, text="no org loop", style="Muted.TLabel")
        self.agent.pack(anchor="w")

    def _attach(self, hid: str):
        def work():
            try:
                snap = self.board.snapshot()
            except Exception as e:
                snap = {}
                err = str(e)
            else:
                err = ""
            active = str(snap.get("active") or "")
            if active in BLOCKED_ACTIVE:
                result = {
                    "ok": False,
                    "id": hid,
                    "live": "FAIL",
                    "copy": GROK_USE,
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
        if self._poll_busy:
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
        if s.get("active_stub"):
            banners.append(f"FAIL: active harness is {s.get('active')} — no grok/opencode fallback")
            banners.append(s.get("blocked_copy") or GROK_USE)
        self.banner_text.configure(text="\n".join(banners) if banners else "window always opens · attach is sidecar")

        d = s.get("detector") or {}
        r = s.get("status_runtime") or {}
        eng_live = honest_live(s.get("engine_live") or d.get("status") or r.get("status"))
        usage = "\n".join(s.get("usage") or []) or "(empty)"
        engine = d.get("engine") or r.get("engine") or "none"
        status = honest_live(d.get("status") or r.get("status"))
        url = d.get("base_url") or r.get("base_url") or "(none)"
        self.local.configure(
            text=f"engine {engine}  {eng_live}\nstatus {status}\nURL {url}\n{usage}\nOllama is an adapter, not the product."
        )
        chips = s.get("chips") or []
        grok = next((c for c in chips if c.get("id") == "grok"), {}) or {}
        grok_live = honest_live(grok.get("live"))
        note = s.get("grok_chip_note") or "Grok chip is PATH-only."
        self.cloud.configure(text=f"grok chip (PATH-only): {grok_live}\nDoD: Grok reviews / sets exit card. Local does bulk.\n{note}")

        tape_bits = []
        for i, t in enumerate(s.get("tape") or [], 1):
            live = t.get("live") or "SKIP"
            tape_bits.append(f"{i}. {t.get('label') or t.get('id')} {live}")
        self.tape.configure(text="   ".join(tape_bits) if tape_bits else "1. inference SKIP   2. env-stage SKIP   3. harness attach SKIP")

        stub = bool(s.get("active_stub"))
        self.btn_grok.configure(state="disabled" if stub else "normal")
        self.btn_opencode.configure(state="disabled" if stub else "normal")
        if stub:
            self.attach_status.configure(text=s.get("blocked_copy") or GROK_USE)
        elif self._attach_msg:
            self.attach_status.configure(text=self._attach_msg)

        for child in self.chips.winfo_children():
            child.destroy()
        tk = sys.modules["tkinter"]
        for c in chips:
            hid = c.get("id") or ""
            live = honest_live(c.get("live"))
            role = c.get("role") or ""
            name = c.get("name") or hid
            fr = tk.Frame(self.chips, bg="#18202c", highlightbackground="#243041", highlightthickness=1, padx=8, pady=6)
            fr.pack(side="left", padx=4, pady=4, anchor="n")
            tk.Label(fr, text=hid, bg="#18202c", fg="#e8edf4", font=("sans-serif", 10, "bold")).pack(anchor="w")
            tk.Label(fr, text=live, bg="#18202c", fg=_chip_color(live), font=("sans-serif", 9, "bold")).pack(anchor="w")
            tk.Label(fr, text=f"{role} · {name}", bg="#18202c", fg="#8b97a8").pack(anchor="w")
            if hid in BLOCKED_ACTIVE:
                tk.Label(fr, text=GROK_USE, bg="#111823", fg="#e8edf4", font=("monospace", 9)).pack(anchor="w", pady=(4, 0))

        verb = (s.get("last_verb") or {}).get("verb") or "(none)"
        when = (s.get("last_verb") or {}).get("when") or ""
        procs = s.get("processes") or []
        ps = ", ".join(f"{p.get('id')}#{p.get('pid')}" for p in procs) or "(none)"
        now_bits = [
            f"attached {s.get('active') or '(none)'}",
            f"last verb {verb} {when}".strip(),
            f"state {s.get('now') or 'idle'} (blocked or running)",
            f"ps: {ps}",
        ]
        if self._attach_msg:
            now_bits.insert(0, self._attach_msg)
        if stub:
            now_bits.insert(0, s.get("blocked_copy") or GROK_USE)
        self.now.configure(text="\n".join(now_bits))

        order_bits = []
        for o in s.get("detect_order") or []:
            mark = "> " if o.get("winner") else ""
            live = honest_live(o.get("live"))
            order_bits.append(f"{mark}{o.get('label')} {o.get('port')} · {live}")
        self.order.configure(text="\n".join(order_bits) if order_bits else "(none)")

        if s.get("agent_lane_collapsed", True):
            self.agent.configure(text="no org loop")
        else:
            rows = s.get("org_messages") or []
            txt = " | ".join(f"{m.get('from')} → {m.get('to')}" for m in rows) or "no org loop"
            self.agent.configure(text=txt)

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


def run_tkinter(board, *, selftest: bool = False) -> int:
    try:
        import tkinter as tk
        import tkinter.ttk  # noqa: F401
    except ImportError:
        print("error: native window toolkit unavailable on this python", file=sys.stderr)
        return 1
    print("native window (tkinter)", flush=True)
    try:
        root = tk.Tk()
    except tk.TclError as e:
        print(f"error: native window failed to open: {e}", file=sys.stderr)
        return 1
    win = TkOperatorWindow(board, root)
    if selftest:
        win._apply(_selftest_snapshot())
        try:
            root.update_idletasks()
            root.update()
        except tk.TclError:
            pass
        title = root.title()
        root.destroy()
        if title != "pfy":
            print("error: window title must be pfy", file=sys.stderr)
            return 1
        return 0
    win.start_polling(int(os.environ.get("PFY_BOARD_REFRESH_MS", "2000")))
    root.mainloop()
    return 0


def main() -> int:
    selftest = os.environ.get("PFY_GUI_SELFTEST") == "1" or "--selftest" in sys.argv
    if selftest:
        return run_tkinter(None, selftest=True)
    board = _load_board()
    try:
        import webview  # noqa: F401
    except ImportError:
        return run_tkinter(board, selftest=False)
    return run_pywebview(board)


if __name__ == "__main__":
    raise SystemExit(main())
