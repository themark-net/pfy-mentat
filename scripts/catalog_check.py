#!/usr/bin/env python3
"""ADR-0015: tools.json is a slim machine subset of TOOLS.md.

Exit 0 if every JSON tool name appears in TOOLS.md.
Does not require JSON row count to match TOOLS.md (~79).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tools = json.loads((ROOT / "data/tools.json").read_text())
md = (ROOT / "TOOLS.md").read_text(encoding="utf-8", errors="replace")
rows = tools.get("tools") or []
missing = [t["name"] for t in rows if t.get("name") and t["name"] not in md]
if missing:
    print("FAIL JSON tools missing from TOOLS.md:", missing)
    sys.exit(1)
print(
    "PASS catalog-check slim-subset ok "
    f"n_json={len(rows)} (not a 1:1 dump of TOOLS.md)"
)
sys.exit(0)
