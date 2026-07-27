#!/usr/bin/env python3
"""Deterministic scorer: voice long-task receipt block (STATUS / DOD / EXIT / NEXT).

Aligns with VOICE_LONG_TASK framing and voice-clean CI receipts.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def score(text: str) -> tuple[bool, str]:
    if not re.search(r"(?im)^\s*STATUS\s*:\s*\S+", text):
        return False, "missing STATUS: line"
    if not re.search(r"(?im)^\s*DOD\s*:\s*\S+", text):
        return False, "missing DOD: line"
    if not re.search(r"(?im)^\s*EXIT\s*:\s*\S+", text):
        return False, "missing EXIT: line"
    if not re.search(r"(?im)^\s*NEXT\s*:\s*\S+", text):
        return False, "missing NEXT: line"
    status_m = re.search(r"(?im)^\s*STATUS\s*:\s*(\S+)", text)
    status = (status_m.group(1) if status_m else "").lower().rstrip(",.;")
    if status not in ("pass", "fail", "blocked", "done", "ok", "error"):
        return False, f"STATUS value not recognized: {status!r}"
    exit_m = re.search(r"(?im)^\s*EXIT\s*:\s*(\S+)", text)
    exit_v = (exit_m.group(1) if exit_m else "").lower().rstrip(",.;")
    allowed_exit = {
        "goal",
        "turn",
        "budget",
        "wall-clock",
        "wall_clock",
        "no-progress",
        "no_progress",
        "human",
        "error",
        "external",
        "done",
        "none",
    }
    if exit_v not in allowed_exit and not any(exit_v.startswith(a) for a in allowed_exit):
        return False, f"EXIT family not recognized: {exit_v!r}"
    return True, f"ok status={status} exit={exit_v}"


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
