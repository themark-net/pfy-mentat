#!/usr/bin/env python3
"""Assembler for scripts/pfy-board.py — cite #155. Concat body parts then exec."""
from pathlib import Path
HERE = Path(__file__).resolve().parent
parts = sorted(HERE.glob("_pfy_board_body_*.py"))
if not parts:
    raise SystemExit("pfy-board: missing _pfy_board_body_*.py parts")
body = "".join(p.read_text() for p in parts)
if len(body) != 51335:
    raise SystemExit(f"pfy-board: bad assembled len {len(body)} want 51335")
exec(compile(body, str(HERE / "pfy-board.py"), "exec"), globals())
