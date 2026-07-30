#!/usr/bin/env python3
"""Deterministic scorer: to-spec / DoD-before-code checklist shape (T-0076)."""
from __future__ import annotations
import re, sys
from pathlib import Path

def score(text: str) -> tuple[bool, str]:
    low = text.lower()
    if not re.search(r"(spec|acceptance|definition of done|requirements|success criteria)", low):
        return False, "missing spec/acceptance framing"
    items = len(re.findall(r"(?m)^\s*(\d+[\).]|[-*])\s+\S+", text))
    if items < 2:
        return False, f"need >=2 checklist items, found {items}"
    if not re.search(r"(test|verify|done when|pass|fail)", low):
        return False, "missing verifiable outcome language"
    return True, f"ok items={items}"

def main() -> int:
    text = sys.stdin.read() if len(sys.argv) < 2 or sys.argv[1] == "-" else Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    ok, detail = score(text)
    print(f"SCORE: {'PASS' if ok else 'FAIL'} ({detail})")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
