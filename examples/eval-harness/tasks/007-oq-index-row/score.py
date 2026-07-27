#!/usr/bin/env python3
"""Structural scorer: Open Question index row or detail shape.

Exit 0 if the document has required OQ structure; 1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def score(text: str) -> tuple[bool, str]:
    t = text.strip()
    if not t:
        return False, "empty"

    has_table_header = bool(
        re.search(
            r"(?im)\|\s*ID\s*\|\s*Priority\s*\|\s*Status\s*\|\s*Title",
            t,
        )
    )
    has_oq_id = bool(re.search(r"(?i)\bOQ-\d{3,4}\b", t))
    has_priority = bool(
        re.search(r"(?im)\*\*?Priority:\*\*?\s*P[0-3]\b", t)
        or re.search(r"(?im)\|\s*P[0-3]\s*\|", t)
        or re.search(r"(?i)\bP[0-3]\b", t)
    )
    has_status = bool(
        re.search(
            r"(?im)\*\*?Status:\*\*?\s*(open|blocked|tbd|answered|promoted-to-adr|wont-do)",
            t,
        )
        or re.search(
            r"(?im)\|\s*(open|blocked|tbd|answered|promoted-to-adr|wont-do)\s*\|",
            t,
        )
    )
    has_question = bool(
        re.search(r"(?im)\*\*?Question:\*\*?", t)
        or re.search(r"(?im)^###\s+OQ-\d+", t)
        or (has_table_header and has_oq_id)
    )

    if has_table_header and has_oq_id and has_priority and has_status:
        return True, "oq index row ok"
    if has_oq_id and has_priority and has_status and has_question:
        return True, "oq detail ok"

    missing = []
    if not has_oq_id:
        missing.append("OQ-ID")
    if not has_priority:
        missing.append("Priority")
    if not has_status:
        missing.append("Status")
    if not has_question and not has_table_header:
        missing.append("Question-or-index")
    return False, "missing: " + ", ".join(missing)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: score.py <file>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8", errors="replace")
    ok, detail = score(text)
    print(("PASS" if ok else "FAIL") + "  " + detail)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
