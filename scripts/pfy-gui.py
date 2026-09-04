#!/usr/bin/env python3
"""Assembler for scripts/pfy-gui.py — cite #153. Concat body parts then exec."""
from pathlib import Path
HERE = Path(__file__).resolve().parent
parts = sorted(HERE.glob("_pfy_gui_body_*.py"))
if not parts:
    raise SystemExit("pfy-gui: missing _pfy_gui_body_*.py parts")
body = "".join(p.read_text() for p in parts)
if len(body) != 32772:
    raise SystemExit(f"pfy-gui: bad assembled len {len(body)} want 32772")
exec(compile(body, str(HERE / "pfy-gui.py"), "exec"), globals())
