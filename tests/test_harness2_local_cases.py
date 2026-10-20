#!/usr/bin/env python3
"""Behavior of the seed-230 split, opaque ids, and the pair scan.

These drive the real cases file. They do not load a model.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cases = _load("h2cases", REPO / "examples" / "harness2-local" / "cases.py")
leaks = _load("h2leaks", REPO / "examples" / "harness2-local" / "leaks.py")


CAUGHT = [
    "ph-01-green-idle: push",
    "wz-07 -> local",
    '"ph-02": "hold"',
    "hd-03 hold",
    "t07 = escalate",
    "t07: local",
    '"t12": "push"',
    "t31 -> skip",
    "T07: local",
    "t07 → hold",
    "t07 is push",
    "PH-03 is push",
    "hd-03 - hold",
    "t07 local",
    "t07, escalate",
    "[t07, push]",
    "t07 push",
    "t07 escalate.",
    "t07\tpush",
]
BENIGN = [
    "Step t10: check CI first.",
    "Step t10 is check CI first",
    "at t00 push the branch",
    "t49: push",
    "t07: hold because CI red",
    "Step t10 push the branch first",
    "see t10, then push the branch",
]


class CaseSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bank = cases.load_bank()
        self.ids = cases.case_ids(self.bank)
        self.labels = sorted({case["label"] for case in self.bank["cases"]})
        self.mapping = cases.id_map(self.ids)

    def test_split_and_map_are_stable(self) -> None:
        self.assertEqual(len(self.ids), 48)
        self.assertEqual(cases.permutation(self.ids), cases.permutation(self.ids))
        self.assertEqual(cases.id_map(self.ids), self.mapping)
        payload = cases.split_payload(self.ids)
        self.assertEqual(len(payload["train_tasks"]), 4)
        self.assertTrue(all(len(task) == 8 for task in payload["train_tasks"]))
        self.assertEqual(len(payload["heldout"]), 16)
        train = [rid for task in payload["train_tasks"] for rid in task]
        self.assertEqual(len(set(train) | set(payload["heldout"])), 48)
        self.assertEqual(cases.canonical(self.mapping), cases.canonical(cases.id_map(self.ids)))

    def test_stripped_file_hash_and_key_order(self) -> None:
        stripped = cases.strip_cases(self.bank["cases"], self.mapping)
        blob = cases.canonical_order(stripped)
        digest = hashlib.sha256(blob.encode()).hexdigest()
        again = hashlib.sha256(
            cases.canonical_order(cases.strip_cases(self.bank["cases"], self.mapping)).encode()
        ).hexdigest()
        self.assertEqual(digest, again)
        label_words = set(self.labels)
        for row in stripped:
            self.assertFalse(set(row) & {"label", "note"})
            self.assertNotIn(row["id"], label_words)
            for word in label_words:
                self.assertNotIn(word, row["id"])
        by_real = {case["id"]: case for case in self.bank["cases"]}
        first = last = 0
        for row in stripped:
            real = next(rid for rid, opaque in self.mapping.items() if opaque == row["id"])
            label = by_real[real]["label"]
            keys = list(row["criteria"])
            first += keys[0] == label
            last += keys[-1] == label
        self.assertTrue(
            11 <= first <= 23 and 11 <= last <= 23,
            f"first={first} last={last}",
        )
        # Order-preserving pin. sort_keys digest 6d6c09cf is identical for a
        # sorted-only strip, so it cannot catch a dropped shuffle.
        self.assertEqual(
            digest,
            "ab0ee29bbe75b46d33248729f9c4dd61376ec357275c8debf6efdb4d296e1b7e",
        )
        # Source order puts the label first in 24 cases, outside the band.
        # Alphabetical order stays inside the band, so only the pinned hash
        # catches a strip that forgot to shuffle.
        source_first = 0
        for case in self.bank["cases"]:
            source_first += list(case["criteria"])[0] == case["label"]
        self.assertGreater(source_first, 23)
        on_disk = json.loads((REPO / "examples" / "harness2-local" / "split.v0.json").read_text())
        self.assertEqual(on_disk, cases.split_payload(self.ids))
        firsts = []
        lasts = []
        for seed in range(1, 201):
            n_first = n_last = 0
            for case in self.bank["cases"]:
                keys = sorted(case["criteria"])
                random.Random(f"{seed}:{case['id']}").shuffle(keys)
                n_first += keys[0] == case["label"]
                n_last += keys[-1] == case["label"]
            firsts.append(n_first)
            lasts.append(n_last)
        self.assertLess(abs(sum(firsts) / len(firsts) - 17.2), 1.5)
        self.assertLess(abs(sum(lasts) / len(lasts) - 17.2), 1.5)

    def test_pair_controls(self) -> None:
        for line in CAUGHT:
            self.assertTrue(leaks.pair_hits(line, self.ids, self.labels), line)
        for line in BENIGN:
            self.assertFalse(leaks.pair_hits(line, self.ids, self.labels), line)
        stripped = cases.strip_cases(self.bank["cases"], self.mapping)
        for blob in (
            cases.canonical(stripped),
            json.dumps(stripped, indent=2),
            "\n".join(json.dumps(row) for row in stripped),
        ):
            self.assertEqual(leaks.pair_hits(blob, self.ids, self.labels), [])


if __name__ == "__main__":
    unittest.main()
