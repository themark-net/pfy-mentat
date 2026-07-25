#!/usr/bin/env python3
"""Deterministic scorer for 003-exit-card-checklist (T-0060).

Usage:
  python3 score.py <path-to-model-output.txt>
  echo "..." | python3 score.py -

Exit 0 + print SCORE: PASS|FAIL
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

EXIT_HINTS = [
    r"goal",
    r"turn",
    r"budget",
    r"wall[\s_-]?clock",
    r"no[\s_-]?progress",
    r"human",
    r"error",
    r"external",
]


def score(text: str) -> tuple[bool, str]:
    low = text.lower()
    if re.search(r"\b(install\s+hermes|must\s+install\s+agenc)\b", low):
        return False, "must not require Hermes/AgenC install"
    if not re.search(r"(exit\s*card|loop\s*exit|eight\s+exit|8\s+exit|exits?\s*:)", low):
        if sum(1 for p in EXIT_HINTS if re.search(p, low)) < 5:
            return False, "missing exit-card framing and too few exit keywords"
    hits = sum(1 for p in EXIT_HINTS if re.search(p, low))
    if hits < 5:
        return False, f"only {hits}/8 exit keyword families (need >=5)"
    if not re.search(r"(goal|dod|success|smoke-grok|definition of done)", low):
        return False, "missing concrete goal/DoD signal"
    return True, f"ok hits={hits}"


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
