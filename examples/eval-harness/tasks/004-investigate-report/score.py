#!/usr/bin/env python3
"""Deterministic scorer: investigate DEBUG REPORT shape (T-0070)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED = [
    r"root\s*cause",
    r"(symptom|observed)",
    r"(fix|changed|patch)",
    r"(status|done|blocked)",
]
FORBIDDEN = [
    r"quick\s+fix\s+without",
    r"no\s+investigation",
]


def score(text: str) -> tuple[bool, str]:
    low = text.lower()
    for p in FORBIDDEN:
        if re.search(p, low):
            return False, f"forbidden pattern: {p}"
    hits = sum(1 for p in REQUIRED if re.search(p, low))
    if hits < 3:
        return False, f"only {hits}/4 report fields"
    if not re.search(r"(hypothesis|confirmed|evidence)", low):
        return False, "missing hypothesis/evidence signal"
    return True, f"ok fields={hits}"


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
