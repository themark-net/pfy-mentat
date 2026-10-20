#!/usr/bin/env python3
"""Id-to-label adjacency scan for stripped files and proposal diffs.

Real ids use the adjacency shape without an end-of-value lookahead.
Opaque ids t01..t48 require the label to end the value, so a sentence
like "Step t10: check CI first." is not a pair.
"""
from __future__ import annotations

import json
import re

_JOIN = r"""["']?\s*(?::|=|->|=>|→|\s-\s|\sis\s|,|\s)\s*["']?"""
_END = r"""(?=\s*(?:$|[.,;:()\]}"']|(?:in)?correct\b|wrong\b|true\b|false\b))"""
_SHORT = r"""(?:wz|hd|ph|fm|cp)-\d{2}"""


def _alt(parts: list[str]) -> str:
    ordered = sorted(set(parts), key=len, reverse=True)
    return "(?:" + "|".join(re.escape(part) for part in ordered) + ")"


def real_pair(real_ids: list[str], labels: list[str]) -> re.Pattern[str]:
    ids = _alt(real_ids)
    labs = _alt(labels)
    return re.compile(
        rf"(?i)(?<![\w-])(?:{ids}|{_SHORT})(?![\w-]){_JOIN}{labs}\b",
    )


def opaque_pair(labels: list[str]) -> re.Pattern[str]:
    labs = _alt(labels)
    return re.compile(
        rf"(?i)(?<![\w-])t(?:0[1-9]|[1-3]\d|4[0-8])(?![\w-]){_JOIN}{labs}\b{_END}",
    )


def pair_hits(text: str, real_ids: list[str], labels: list[str]) -> list[str]:
    found = []
    for pat in (real_pair(real_ids, labels), opaque_pair(labels)):
        found.extend(match.group(0) for match in pat.finditer(text))
    return found


_SHORT_ID = re.compile(r"(?i)(?<![\w-])(?:wz|hd|ph|fm|cp)-\d{2}(?!\d)")


def short_id_hits(text: str) -> list[str]:
    return _SHORT_ID.findall(text)


def real_id_hits(text: str, real_ids: list[str]) -> list[str]:
    if not real_ids:
        return []
    pat = re.compile(rf"(?i)(?<![\w-])(?:{_alt(real_ids)})(?![\w-])")
    return pat.findall(text)


def note_hits(text: str, notes: list[str]) -> list[str]:
    return [note for note in notes if len(note) >= 20 and note in text]


def answer_pair_text(text: str) -> str:
    """Drop executor ``why`` values. Model free text is not a leak we wrote."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return text
    answers = obj.get("answers") if isinstance(obj, dict) else None
    if not isinstance(answers, list):
        return text
    kept = []
    for row in answers:
        if isinstance(row, dict):
            kept.append({k: v for k, v in row.items() if k != "why"})
        else:
            kept.append(row)
    return json.dumps({"answers": kept})
