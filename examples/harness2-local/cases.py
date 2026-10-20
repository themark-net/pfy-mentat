#!/usr/bin/env python3
"""Case load, seed-230 split, opaque ids, and deterministic scoring.

The id map and the split share one shuffle: sorted real ids, then
random.Random(230).shuffle. Train is the first 32, in four tasks of 8.
Held-out is the last 16. Scoring follows examples/typed-decisions-local/trial.py:
correct is choice == label, escalate is confidence below the file's conf_gate.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CASES_PATH = REPO / "data" / "decision-gates" / "laya-trial.cases.v0.json"
SPLIT_PATH = Path(__file__).resolve().parent / "split.v0.json"
SEED = 230


def load_bank(path: Path | None = None) -> dict:
    return json.loads((path or CASES_PATH).read_text(encoding="utf-8"))


def case_ids(bank: dict) -> list[str]:
    return [case["id"] for case in bank["cases"]]


def permutation(real_ids: list[str], seed: int = SEED) -> list[str]:
    ids = sorted(real_ids)
    random.Random(seed).shuffle(ids)
    return ids


def id_map(real_ids: list[str], seed: int = SEED) -> dict[str, str]:
    return {rid: f"t{i:02d}" for i, rid in enumerate(permutation(real_ids, seed), 1)}


def split_payload(real_ids: list[str], seed: int = SEED) -> dict:
    order = permutation(real_ids, seed)
    if len(order) < 48:
        raise ValueError(f"need 48 cases to split, got {len(order)}")
    train = order[:32]
    return {
        "seed": seed,
        "train_tasks": [train[i : i + 8] for i in range(0, 32, 8)],
        "heldout": order[32:48],
    }


def canonical(obj: object) -> str:
    """Sorted-key JSON. Right for the id map. It erases criteria order."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_order(obj: object) -> str:
    """JSON that keeps dict order. The stripped-file pin uses this so a
    dropped criteria shuffle changes the digest. ``canonical`` does not.
    """
    return json.dumps(obj, ensure_ascii=False, sort_keys=False, separators=(",", ":"))


def shuffled_criteria(real_id: str, criteria: dict, seed: int = SEED) -> dict:
    keys = sorted(criteria)
    random.Random(f"{seed}:{real_id}").shuffle(keys)
    return {key: criteria[key] for key in keys}


def strip_case(case: dict, opaque: str, seed: int = SEED) -> dict:
    """Executor view: no label, no note, no real id. Criteria order is shuffled."""
    return {
        "id": opaque,
        "instructions": case.get("instructions") or "",
        "state": case.get("state"),
        "criteria": shuffled_criteria(case["id"], case["criteria"], seed),
    }


def strip_cases(cases: list[dict], mapping: dict[str, str], seed: int = SEED) -> list[dict]:
    return [strip_case(case, mapping[case["id"]], seed) for case in cases]


def score_batch(
    cases: list[dict],
    answers: list[dict],
    *,
    gate: float,
) -> dict:
    """Score opaque answers against cases that still carry label and criteria.

    cases are the original records. answers use opaque ids. The caller passes
    cases already filtered to this batch, and answers whose "case" matches
    each case's opaque id via `opaque_of`.
    """
    by_opaque = {row.get("case"): row for row in answers}
    n = len(cases)
    n_correct = 0
    n_escalate = 0
    n_wbc = 0
    n_parse = 0
    for case in cases:
        row = by_opaque.get(case["opaque"])
        choice = row.get("choice") if isinstance(row, dict) else None
        try:
            conf = float(row.get("confidence")) if isinstance(row, dict) else None
        except (TypeError, ValueError):
            conf = None
        keys = set(case["criteria"])
        parsed = isinstance(choice, str) and choice in keys and conf is not None and 0.0 <= conf <= 1.0
        if not parsed:
            continue
        n_parse += 1
        correct = choice == case["label"]
        escalate = conf < gate
        if correct:
            n_correct += 1
        if escalate:
            n_escalate += 1
        if not correct and not escalate:
            n_wbc += 1
    return {
        "n": n,
        "n_correct": n_correct,
        "n_escalate": n_escalate,
        "wrong_but_confident": n_wbc,
        "n_parse_ok": n_parse,
        "parse_ok": 0.0 if n == 0 else n_parse / n,
        "accuracy": 0.0 if n == 0 else n_correct / n,
    }
