"""pfylib.hedge: deterministic local-first lane policy + ledger (ADR-0017)."""
from __future__ import annotations

import json
import os
import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import hedge  # noqa: E402

READY = {"engine": "ollama", "base_url": "http://127.0.0.1:11434/v1", "status": "ready"}
MISSING = {"engine": "none", "base_url": "", "status": "missing"}


class _Tmp(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("PFY_CLOUD_BUDGET", "PFY_CLOUD_TASK_COST", "DEPLOY_PROFILE", "PFY_STATE_DIR")}
        for k in self._saved:
            os.environ.pop(k, None)
        self.state = Path(tempfile.mkdtemp(prefix="pfylib-hedge-"))

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def decide(self, task, local, budget, **kw):
        return hedge.decide(task, local=local, budget=budget, state=self.state, deploy_profile="", **kw)


class DecisionMatrixTests(_Tmp):
    """3 task classes x (local ready / missing) x (budget yes / no)."""

    EXPECTED = {
        # (task, local_ready, budget) -> lane or None (FAIL)
        ("bulk", True, True): "local",
        ("bulk", True, False): "local",
        ("bulk", False, True): "cloud",
        ("bulk", False, False): None,
        ("interactive", True, True): "local",
        ("interactive", True, False): "local",
        ("interactive", False, True): "cloud",
        ("interactive", False, False): None,
        ("hard", True, True): "cloud",
        ("hard", True, False): "local",
        ("hard", False, True): "cloud",
        ("hard", False, False): None,
    }

    def test_all_twelve_cells(self):
        for (task, local_ready, has_budget), lane in self.EXPECTED.items():
            rec = self.decide(task, READY if local_ready else MISSING, 5 if has_budget else 0)
            with self.subTest(task=task, local=local_ready, budget=has_budget):
                self.assertEqual(rec["lane"], lane, rec["copy"])
                self.assertEqual(rec["ok"], lane is not None)
                self.assertEqual(rec["live"], "READY" if lane else "FAIL")
                self.assertTrue(rec["reason"])
                if lane is None:
                    self.assertIn("PFY_CLOUD_BUDGET", rec["next_step"])
                else:
                    self.assertEqual(rec["next_step"], "")
                self.assertEqual(rec["task"], task)

    def test_deterministic(self):
        a = self.decide("hard", READY, 3)
        b = self.decide("hard", READY, 3)
        self.assertEqual(a, b)

    def test_unknown_task_fails(self):
        rec = self.decide("chat", READY, 5)
        self.assertEqual(rec["live"], "FAIL")
        self.assertIn("bulk|hard|interactive", rec["next_step"])

    def test_local_only_profile_forbids_cloud(self):
        rec = hedge.decide("hard", local=MISSING, budget=99, state=self.state, deploy_profile="local-only")
        self.assertEqual(rec["live"], "FAIL")
        self.assertIn("local-only", rec["reason"])
        rec = hedge.decide("hard", local=READY, budget=99, state=self.state, deploy_profile="local-only")
        self.assertEqual(rec["lane"], "local")

    def test_only_ready_status_counts_as_local(self):
        for st in ("missing", "degraded", "", "READY-ish"):
            rec = self.decide("bulk", {"engine": "x", "base_url": "", "status": st}, 0)
            self.assertEqual(rec["live"], "FAIL", st)
        rec = self.decide("bulk", {"engine": "x", "base_url": "", "status": "READY"}, 0)
        self.assertEqual(rec["lane"], "local")

    def test_cost_gates_remaining_budget(self):
        rec = self.decide("hard", MISSING, 2, cost=3)
        self.assertEqual(rec["live"], "FAIL")
        self.assertIn("remaining 2 < cost 3", rec["reason"])
        rec = self.decide("hard", MISSING, 3, cost=3)
        self.assertEqual(rec["lane"], "cloud")

    def test_budget_from_env_when_not_passed(self):
        os.environ["PFY_CLOUD_BUDGET"] = "4"
        rec = hedge.decide("hard", local=MISSING, state=self.state, deploy_profile="")
        self.assertEqual(rec["lane"], "cloud")
        self.assertEqual(rec["budget"], 4)
        os.environ["PFY_CLOUD_BUDGET"] = "not-a-number"
        self.assertEqual(hedge.budget_from_env(), 0)


class LedgerTests(_Tmp):
    def test_round_trip(self):
        path = hedge.ledger_path(self.state)
        self.assertFalse(path.exists())
        self.assertEqual(hedge.load_ledger(self.state)["spent"], 0)
        r = hedge.record(3, lane="cloud", task="hard", note="t", state=self.state, budget=10)
        self.assertTrue(r["ok"])
        self.assertEqual((r["spent"], r["remaining"]), (3, 7))
        self.assertTrue(path.is_file())
        led = hedge.load_ledger(self.state)
        self.assertEqual(led["spent"], 3)
        self.assertEqual(len(led["entries"]), 1)
        self.assertEqual(led["entries"][0]["task"], "hard")
        raw = json.loads(path.read_text())
        self.assertEqual(raw["version"], 1)
        self.assertIn("updated", raw)

    def test_local_entries_cost_nothing(self):
        r = hedge.record(5, lane="local", state=self.state, budget=10)
        self.assertEqual(r["amount"], 0)
        self.assertEqual(hedge.load_ledger(self.state)["spent"], 0)

    def test_spent_is_recomputed_from_entries(self):
        hedge.record(2, state=self.state, budget=10)
        hedge.record(2, state=self.state, budget=10)
        self.assertEqual(hedge.load_ledger(self.state)["spent"], 4)

    def test_spend_reduces_remaining_and_flips_decision(self):
        self.assertEqual(self.decide("hard", MISSING, 2)["lane"], "cloud")
        hedge.record(2, state=self.state, budget=2)
        rec = self.decide("hard", MISSING, 2)
        self.assertEqual(rec["live"], "FAIL")
        self.assertEqual(rec["remaining"], 0)

    def test_decide_and_record_debits_only_cloud(self):
        rec = hedge.decide_and_record("hard", local=MISSING, budget=3, state=self.state, deploy_profile="")
        self.assertEqual(rec["lane"], "cloud")
        self.assertEqual(rec["recorded"], 1)
        self.assertEqual(rec["remaining"], 2)
        rec = hedge.decide_and_record("bulk", local=READY, budget=3, state=self.state, deploy_profile="")
        self.assertEqual(rec["lane"], "local")
        self.assertNotIn("recorded", rec)
        self.assertEqual(hedge.load_ledger(self.state)["spent"], 1)

    def test_unknown_lane_and_reset(self):
        r = hedge.record(1, lane="edge", state=self.state)
        self.assertFalse(r["ok"])
        hedge.record(1, state=self.state, budget=1)
        hedge.reset_ledger(self.state)
        self.assertEqual(hedge.load_ledger(self.state)["spent"], 0)

    def test_unreadable_ledger_is_treated_as_empty(self):
        path = hedge.ledger_path(self.state)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json")
        led = hedge.load_ledger(self.state)
        self.assertEqual(led["spent"], 0)
        self.assertIn("error", led)


class DetectorTests(unittest.TestCase):
    def test_missing_detector_is_honest(self):
        with tempfile.TemporaryDirectory() as d:
            rec = hedge.detect_local(Path(d))
        self.assertEqual(rec["status"], "missing")
        self.assertIn("error", rec)

    def test_detector_runs_offline(self):
        rec = hedge.detect_local(ROOT, timeout=20)
        self.assertIn(rec["status"], ("ready", "missing", "degraded"))
        self.assertIn("engine", rec)


if __name__ == "__main__":
    unittest.main()
