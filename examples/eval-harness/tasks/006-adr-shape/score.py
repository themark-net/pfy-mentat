#!/usr/bin/env python3
"""Deterministic scorer: multi-file ADR shape (T-0075)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def score(text: str) -> tuple[bool, str]:
    if not re.search(r"(?m)^#\s+ADR-\d{4}:", text):
        return False, "missing # ADR-NNNN: title"
    if not re.search(r"\*\*Status:\*\*\s*\S+", text) and not re.search(
        r"(?m)^-\s+\*\*Status:\*\*", text
    ):
        return False, "missing Status field"
    if not re.search(r"(?m)^##\s+Context\b", text):
        return False, "missing ## Context"
    if not re.search(r"(?m)^##\s+Decision\b", text):
        return False, "missing ## Decision"
    if not re.search(r"(?m)^##\s+Consequences\b", text):
        return False, "missing ## Consequences"
    # Rejected alternatives or paths decided against (ADR-0001)
    if not re.search(r"(?i)(rejected|decided against|not chosen|alternative)", text):
        return False, "missing rejected alternatives / paths decided against"
    return True, "ok ADR shape"


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
