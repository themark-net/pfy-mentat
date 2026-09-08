#!/usr/bin/env python3
"""Enterable OpenCode open_enterable -- cite #162 (b) / #181 / #193.

Assembles pfy_enterable_162_b_p0.py + _p1a.py + _p1b.py (board-style parts).
"""
from __future__ import annotations
from pathlib import Path
_HERE = Path(__file__).resolve().parent
_parts = []
for _name in ("pfy_enterable_162_b_p0.py", "pfy_enterable_162_b_p1a.py", "pfy_enterable_162_b_p1b.py"):
    _p = _HERE / _name
    if not _p.is_file():
        raise SystemExit("pfy_enterable_162_b: missing " + _name)
    _parts.append(_p.read_text(encoding="utf-8"))
_body = "".join(_parts)
if len(_body) < 10000:
    raise SystemExit(f"pfy_enterable_162_b: bad assembled len {len(_body)}")
exec(compile(_body, str(Path(__file__).resolve()), "exec"), globals())
