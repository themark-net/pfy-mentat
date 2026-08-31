#!/usr/bin/env python3
"""Restore scripts/pfy if emptied/truncated; drop cargo/pywebview launch one-liners."""
from pathlib import Path
import urllib.request

MAIN = "22a2f2448f9565643ac1b62fa5f9c6026547eb1a"
URL = f"https://raw.githubusercontent.com/themark-net/pfy-mentat/{MAIN}/scripts/pfy"
OLD_LAUNCH = (
    '    echo "native window (pywebview)"\n'
    '    echo "  one-liner: cd gui/operator/src-tauri && cargo build --release"\n'
    '    exec python3 "$ROOT/scripts/pfy-gui.py"\n'
)
NEW_LAUNCH = '    exec python3 "$ROOT/scripts/pfy-gui.py"\n'
REPLACES = [
    (
        "Native window is the main interface (Tauri if built, else pywebview / webkit / tkinter).\n",
        "Native window is the main interface. Tauri if pfy-operator exists; else webkit or stdlib tk.\n",
    ),
    (
        "Native window is the main interface. Tauri binary (when built):\n"
        "  cd gui/operator/src-tauri && cargo build --release\n"
        "  \u2192 gui/operator/src-tauri/target/release/pfy-operator\n"
        "Else pywebview + WebKitGTK (scripts/pfy-gui.py). Missing pywebview: install tip, exit 2.\n",
        "Native window is the main interface. Tauri if pfy-operator exists; else webkit or stdlib tk.\n",
    ),
    (
        "  pfy board [--open]      alias of the native operator window (Tauri if built, else pywebview)\n",
        "  pfy board [--open]      alias of the native operator window (Tauri / webkit / tk)\n",
    ),
]


def main() -> None:
    p = Path("scripts/pfy")
    if not p.exists() or p.stat().st_size < 25000:
        print("scripts/pfy empty/truncated — restoring from", MAIN, "size", p.stat().st_size if p.exists() else 0)
        p.write_bytes(urllib.request.urlopen(URL, timeout=30).read())
    t = p.read_text()
    if OLD_LAUNCH in t:
        t = t.replace(OLD_LAUNCH, NEW_LAUNCH, 1)
        print("dropped cargo/pywebview launch one-liners")
    for old, new in REPLACES:
        if old in t:
            t = t.replace(old, new, 1)
            print("replaced usage block")
    t = t.replace('die "native GUI missing (scripts/pfy-gui.py)"',
                  'die "native window could not open (scripts/pfy-gui.py missing)"')
    p.write_text(t)
    print("scripts/pfy bytes", p.stat().st_size)
    if p.stat().st_size < 25000:
        raise SystemExit("scripts/pfy still truncated after restore")


if __name__ == "__main__":
    main()
