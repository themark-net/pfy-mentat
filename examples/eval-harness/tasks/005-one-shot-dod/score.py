#!/usr/bin/env python3
"""Deterministic scorer: one-shot DoD checklist shape (T-0070)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def score(text: str) -> tuple[bool, str]:
    low = text.lower()
    if not re.search(r"(definition of done|dod\b|success criteria)", low):
        return False, "missing DoD framing"
    # Need numbered or bullet pass/fail style checks
    checks = len(re.findall(r"(?m)^\s*(\d+[\).]|[-*])\s+\S+", text))
    if checks < 2:
        return False, f"need >=2 checklist items, found {checks}"
    if not re.search(r"(make\s+\S+|exit\s*0|pass|green|command)", low):
        return False, "missing verifiable command/outcome signal"
    if re.search(r"infinite\s+retry|yolo\s+until", low):
        return False, "forbidden unbounded loop language"
    return True, f"ok checks={checks}"


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "-":
        text = sys.stdin.read()
    else:
        text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    ok, detail = score(text)
    print(f"SCORE: {'PASS' if ok else 'FAIL'} ({detail})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
