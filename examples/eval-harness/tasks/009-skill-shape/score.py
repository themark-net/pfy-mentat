#!/usr/bin/env python3
"""Skill SKILL.md shape: name + description + body (T-0070)."""
from __future__ import annotations
import re, sys
from pathlib import Path

def score(text: str) -> tuple[bool, str]:
    if not re.search(r"(?m)^#\s+\S+", text):
        return False, "missing H1 title"
    if len(text.strip()) < 120:
        return False, "too short"
    if not re.search(r"(when to use|usage|steps|do not|non-goal|invoke)", text, re.I):
        return False, "missing usage/when-to-use style section"
    return True, "ok"

def main() -> int:
    text = sys.stdin.read() if len(sys.argv) < 2 or sys.argv[1] == "-" else Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    ok, d = score(text)
    print(f"SCORE: {'PASS' if ok else 'FAIL'} ({d})")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
