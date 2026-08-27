#!/usr/bin/env python3
"""Native operator window (pywebview + WebKitGTK). Same IA as the Tauri frontend.

Always-works fallback when gui/operator/src-tauri/target/release/pfy-operator
is not built. Not Electron. Not a second daemon: HTTP poller runs in-process.
"""
from __future__ import annotations

import importlib.util
import os
import socket
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def main() -> int:
    try:
        import webview
    except ImportError:
        print("STUB: pywebview not installed. Native window needs pywebview + WebKitGTK.")
        print("  python3 -m pip install pywebview")
        print("  # Debian/Ubuntu: sudo apt install python3-webview gir1.2-webkit2-4.1")
        print("  # Tauri is primary when built (no extra Python GUI dep):")
        print("  cd gui/operator/src-tauri && cargo build --release")
        print("  # binary: gui/operator/src-tauri/target/release/pfy-operator")
        return 2

    board = _load_board()
    host = getattr(board, "HOST", os.environ.get("PFY_BOARD_HOST", "127.0.0.1"))
    port = int(getattr(board, "PORT", os.environ.get("PFY_BOARD_PORT", "8765")))
    url = f"http://{host}:{port}/"
    httpd = None
    if not _port_open(host, port):
        from http.server import ThreadingHTTPServer

        httpd = ThreadingHTTPServer((host, port), board.Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print("pfy native GUI (pywebview)")
        print(f"  {url}")
        print("  in-process poller · grok/opencode attach = sidecar · not a supervisor")
    else:
        print("pfy native GUI (pywebview)")
        print(f"  {url} (existing local board)")
    webview.create_window("pfy", url, width=1280, height=900)
    webview.start()
    if httpd is not None:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
