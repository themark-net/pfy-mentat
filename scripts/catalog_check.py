#!/usr/bin/env python3
"""GAP-03 catalog triple soft checks. Exit 0 if S-tier names in TOOLS.md."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tools = json.loads((ROOT / "data/tools.json").read_text())
md = (ROOT / "TOOLS.md").read_text(encoding="utf-8", errors="replace")
missing = [t["name"] for t in tools["tools"] if t.get("tier") == "S" and t["name"] not in md]
if missing:
    print("FAIL S-tier missing from TOOLS.md:", missing)
    sys.exit(1)
print(f"PASS catalog-check S-tier ok n={len(tools['tools'])}")
sys.exit(0)
