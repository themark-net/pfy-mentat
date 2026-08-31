#!/usr/bin/env python3
"""Restore truncated scripts/pfy; drop cargo launch stubs; spec print labels."""
from pathlib import Path
import urllib.request

MAIN = "22a2f2448f9565643ac1b62fa5f9c6026547eb1a"
URL = f"https://raw.githubusercontent.com/themark-net/pfy-mentat/{MAIN}/scripts/pfy"
OLD_LAUNCH = (
    '    echo "native window (pywebview)"\n'
    '    echo "  one-liner: cd gui/operator/src-tauri && cargo build --release"\n'
    '    exec python3 "$ROOT/scripts/pfy-gui.py"\n'
)
NEW_LAUNCH = (
    '    # pfy-gui.py prints native window (pywebview|webkit|tkinter); never cargo/pip/apt\n'
    '    exec python3 "$ROOT/scripts/pfy-gui.py"\n'
)
OLD_USAGE = (
    "Native window is the main interface. Tauri binary (when built):\n"
    "  cd gui/operator/src-tauri && cargo build --release\n"
    "  \u2192 gui/operator/src-tauri/target/release/pfy-operator\n"
    "Else pywebview + WebKitGTK (scripts/pfy-gui.py). Missing pywebview: install tip, exit 2.\n"
)
NEW_USAGE = (
    "Native window is the main interface (Tauri if built, else pywebview / webkit / tkinter).\n"
)
OLD_BOARD = (
    "  pfy board [--open]      alias of the native operator window (Tauri if built, else pywebview)\n"
)
NEW_BOARD = "  pfy board [--open]      alias of the native operator window\n"


def restore_launcher() -> None:
    p = Path("scripts/pfy")
    t = p.read_text() if p.exists() else ""
    truncated = (not p.exists()) or p.stat().st_size < 30000 or 'main "$@"' not in t
    if truncated:
        print("scripts/pfy truncated/broken — restoring from", MAIN)
        p.write_bytes(urllib.request.urlopen(URL, timeout=30).read())
        t = p.read_text()
    if OLD_LAUNCH in t:
        t = t.replace(OLD_LAUNCH, NEW_LAUNCH, 1)
        print("dropped cargo/pywebview launch one-liners")
    if OLD_USAGE in t:
        t = t.replace(OLD_USAGE, NEW_USAGE, 1)
        print("dropped cargo usage install tip")
    if OLD_BOARD in t:
        t = t.replace(OLD_BOARD, NEW_BOARD, 1)
    p.write_text(t)
    print("scripts/pfy bytes", p.stat().st_size, "has main", 'main "$@"' in t)


def patch_gui() -> None:
    p = Path("scripts/pfy-gui.py")
    if not p.exists():
        return
    t = p.read_text()
    if 'print("native window (tk)"' in t:
        t = t.replace('print("native window (tk)"', 'print("native window (tkinter)"')
        print("relabeled native window (tk) -> (tkinter)")
    p.write_text(t)


def main() -> None:
    restore_launcher()
    patch_gui()


if __name__ == "__main__":
    main()
