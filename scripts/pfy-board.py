#!/usr/bin/env python3
"""Loader: assemble board body parts then exec (write-path workaround for #150)."""
from pathlib import Path
_dir = Path(__file__).resolve().parent
_body = "".join((_dir / f"_pfy_board_body_{i}.py").read_text(encoding="utf-8") for i in range(3))
exec(compile(_body, str(_dir / "pfy-board.py"), "exec"), globals())
