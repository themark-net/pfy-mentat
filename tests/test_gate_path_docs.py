"""A test-adding pin must not fast-forward on pregate alone.

Fail: the gate docs drop the requirement to dispatch eval-structural at the
fix pin and wait for both G0 jobs. A bot then fast-forwards a docs pin whose
new tests never ran on a depth-1 checkout.
Recovery: put the rule back in docs/build-dropins/common-rules.md and the
ops gate docs. Do not treat a local pregate PASS as that dispatch.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JOBS = ("G0 (ubuntu-24.04)", "G0 (self-hosted nimo)")

GATE_DOCS = (
    "docs/build-dropins/common-rules.md",
    "docs/ops/PREGATE.md",
    "docs/ops/eval-gates-and-ux-uat.md",
    "docs/ops/HANDOFF-pregate.md",
)

DROP_INS = (
    "docs/build-dropins/mvp-backlog-fu-1031.md",
    "docs/build-dropins/backlog-catalog-1030.md",
    "docs/build-dropins/pfy-followups-1030.md",
)


def fast_forward_waits_for_both_g0_jobs(text: str) -> bool:
    """True only when the text blocks a fast-forward until both G0 jobs finish."""
    lowered = text.lower()
    if "eval-structural" not in lowered or "fix pin" not in lowered:
        return False
    if "fast-forward" not in lowered:
        return False
    if "pregate" not in lowered or "both" not in lowered:
        return False
    return all(job in text for job in JOBS)


class GatePathDocsTests(unittest.TestCase):
    def test_old_pregate_sentence_does_not_wait_for_both_jobs(self):
        old = (
            "the gate needed (Tester plus Reviewer for runtime changes; "
            "pregate plus Reviewer for docs, eval or test-only changes), "
            "and the next step. Fast-forward main after pregate PASS."
        )
        self.assertFalse(fast_forward_waits_for_both_g0_jobs(old))

    def test_gate_docs_dispatch_eval_structural_before_fast_forward(self):
        for rel in GATE_DOCS:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertTrue(
                fast_forward_waits_for_both_g0_jobs(text),
                rel,
            )
        for rel in GATE_DOCS[1:]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("common-rules.md", text, rel)

    def test_drop_in_finish_lines_point_at_the_common_rule(self):
        for rel in DROP_INS:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("common-rules.md", text, rel)
            self.assertIn("both G0 jobs", text, rel)
            self.assertIn("fix pin", text, rel)
            self.assertIn("pregate PASS does not replace", text, rel)


if __name__ == "__main__":
    unittest.main()
