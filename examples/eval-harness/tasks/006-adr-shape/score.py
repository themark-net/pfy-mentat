#!/usr/bin/env python3
"""Structural scorer: ADR shape (multi-file or single-file form).

Exit 0 if the document has required sections; 1 otherwise.
Used by run_structural.py via fixtures/pass* and fixtures/fail*.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def score(text: str) -> tuple[bool, str]:
    t = text.strip()
    if not t:
        return False, "empty"

    # Status line or bullet
    has_status = bool(
        re.search(r"(?im)^\*\*?Status:\*\*?\s*(Proposed|Accepted|Rejected|Superseded)", t)
        or re.search(r"(?im)^-\s+\*\*?Status:\*\*?\s*(Proposed|Accepted|Rejected|Superseded)", t)
        or re.search(r"(?im)^##\s+Decision\s+\d+.*\n(?:.*\n)*?\*\*?Status:\*\*?", t)
    )

    has_context = bool(
        re.search(r"(?im)^##\s+Context\b", t)
        or re.search(r"(?im)^\*\*?Context:\*\*?", t)
    )
    has_decision = bool(
        re.search(r"(?im)^##\s+Decision\b", t)
        or re.search(r"(?im)^\*\*?Decision:\*\*?", t)
    )
    has_rationale = bool(
        re.search(r"(?im)^##\s+Rationale\b", t)
        or re.search(r"(?im)^\*\*?Rationale:\*\*?", t)
    )
    # Rejected alternatives signal (explicit requirement in template)
    has_rejected = bool(
        re.search(r"(?i)rejected\s+alternatives?", t)
        or re.search(r"(?i)alternatives?\s+(rejected|set aside|considered)", t)
    )
    has_consequences = bool(
        re.search(r"(?im)^##\s+Consequences\b", t)
        or re.search(r"(?im)^\*\*?Consequences:\*\*?", t)
    )

    missing = []
    if not has_status:
        missing.append("Status")
    if not has_context:
        missing.append("Context")
    if not has_decision:
        missing.append("Decision")
    if not has_rationale:
        missing.append("Rationale")
    if not has_rejected:
        missing.append("rejected-alternatives")
    if not has_consequences:
        missing.append("Consequences")

    if missing:
        return False, "missing: " + ", ".join(missing)
    return True, "adr shape ok"


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
