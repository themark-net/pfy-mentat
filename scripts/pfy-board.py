#!/usr/bin/env python3
"""Assembler for scripts/pfy-board.py — cite #153. Concat body parts then exec."""
from pathlib import Path
HERE = Path(__file__).resolve().parent
parts = sorted(HERE.glob("_pfy_board_body_*.py"))
if not parts:
    raise SystemExit("pfy-board: missing _pfy_board_body_*.py parts")
body = "".join(p.read_text() for p in parts)
if len(body) != 50201:
    raise SystemExit(f"pfy-board: bad assembled len {len(body)} want 50201")
exec(compile(body, str(HERE / "pfy-board.py"), "exec"), globals())
