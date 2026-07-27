#!/usr/bin/env python3
"""Deterministic scorer: voice long-task receipt block (STATUS / DOD / EXIT / NEXT).

Aligns with VOICE_LONG_TASK framing and voice-clean CI receipts.

Beyond label presence: values must be recognized; all four labels must appear
as line-start keys (noise preamble allowed). Stricter than a greppable blob.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

STATUS_OK = frozenset({"pass", "fail", "blocked", "done", "ok", "error"})
EXIT_OK = frozenset(
    {
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
)


def _line_val(text: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{key}\s*:\s*(\S+.*)$", text)
    if not m:
        return None
    return m.group(1).strip()


def score(text: str) -> tuple[bool, str]:
    if not text or not text.strip():
        return False, "empty text"
    status_raw = _line_val(text, "STATUS")
    dod_raw = _line_val(text, "DOD")
    exit_raw = _line_val(text, "EXIT")
    next_raw = _line_val(text, "NEXT")
    if not status_raw:
        return False, "missing STATUS: line"
    if not dod_raw:
        return False, "missing DOD: line"
    if not exit_raw:
        return False, "missing EXIT: line"
    if not next_raw:
        return False, "missing NEXT: line"
    # DOD/NEXT need more than a punctuation token
    if len(re.sub(r"[\W_]+", "", dod_raw)) < 2:
        return False, "DOD value too thin"
    if len(re.sub(r"[\W_]+", "", next_raw)) < 2:
        return False, "NEXT value too thin"
    status = status_raw.split()[0].lower().rstrip(",.;")
    if status not in STATUS_OK:
        return False, f"STATUS value not recognized: {status!r}"
    exit_v = exit_raw.split()[0].lower().rstrip(",.;")
    if exit_v not in EXIT_OK and not any(exit_v.startswith(a) for a in EXIT_OK):
        return False, f"EXIT family not recognized: {exit_v!r}"
    # Prefer receipt near end (last 40% or last 12 lines) — still pass if earlier
    lines = [ln for ln in text.splitlines() if ln.strip()]
    tail = "\n".join(lines[-max(12, len(lines) // 3) :])
    in_tail = all(
        re.search(rf"(?im)^\s*{k}\s*:", tail) for k in ("STATUS", "DOD", "EXIT", "NEXT")
    )
    where = "tail" if in_tail else "body"
    return True, f"ok status={status} exit={exit_v} placement={where}"


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
