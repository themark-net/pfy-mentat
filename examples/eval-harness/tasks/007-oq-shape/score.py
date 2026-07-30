#!/usr/bin/env python3
"""Deterministic scorer: open-question detail file shape (T-0075)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def score(text: str) -> tuple[bool, str]:
    if not re.search(r"(?m)^#\s+OQ-\d{4}:", text):
        return False, "missing # OQ-NNNN: title"
    if not re.search(r"\*\*Status:\*\*|\*\*Priority:\*\*", text):
        return False, "missing Priority/Status metadata"
    if not re.search(r"(?i)\*\*Question:\*\*|\*\*question:\*\*", text):
        return False, "missing Question field"
    if not re.search(r"(?i)(options|resolution notes)", text):
        return False, "missing Options or Resolution notes"
    return True, "ok OQ shape"


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
