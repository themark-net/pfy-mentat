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
