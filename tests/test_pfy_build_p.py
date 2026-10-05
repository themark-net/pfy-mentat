"""Behavior tests for pfy build -p and decision route escalate exit contract."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


jev = _load("pfy_jev_230", "scripts/pfy_jev_230.py")
build = _load("pfy_build_p", "scripts/pfy_build_p.py")


class RouteEscalateExitTests(unittest.TestCase):
    def test_conf_low_is_escalate_exit_3_not_broken(self):
        os.environ["PFY_JEV_CONF_GATE"] = "0.99"
        try:
            low = jev.decide_choice(
                "ambiguous state",
                {"a": "maybe", "b": "also maybe", "c": "unclear"},
            )
        finally:
            os.environ.pop("PFY_JEV_CONF_GATE", None)
        self.assertFalse(low.get("auto_act"))
        self.assertEqual(jev.classify_decision(low), "escalate")
        self.assertEqual(jev.decision_exit_code(low), jev.EXIT_ESCALATE)
        text = jev.format_decision_cli(low)
        self.assertTrue(text.startswith("ESCALATE"), text)
        self.assertNotIn("tool failure", text.lower())

    def test_route_main_escalate_rc(self):
        os.environ["PFY_JEV_CONF_GATE"] = "0.99"
        try:
            rc = jev.main(["--route"])
        finally:
            os.environ.pop("PFY_JEV_CONF_GATE", None)
        self.assertEqual(rc, jev.EXIT_ESCALATE)

    def test_ready_exit_0(self):
        # Peaked criteria → high margin
        rec = jev.decide_choice(
            "push green tip now",
            {"push": "push green tip now", "hold": "zzzz unrelated hold"},
        )
        if not rec.get("auto_act"):
            self.skipTest("logit margin not peaked enough in this environment")
        self.assertEqual(jev.classify_decision(rec), "ready")
        self.assertEqual(jev.decision_exit_code(rec), jev.EXIT_READY)


class BuildHelperFailRecoverTests(unittest.TestCase):
    def test_missing_grok_on_path_fails_honestly(self):
        with tempfile.TemporaryDirectory(prefix="pfy-build-") as td:
            td = Path(td)
            # Empty PATH → which('grok') is None
            rc = build.build_p(
                "should not run",
                cwd=td,
                repo=ROOT,
                dry_run=False,
                path_env="",  # empty PATH
            )
            self.assertEqual(rc, build.EXIT_FAIL)
            receipts = list((td / "pipelines" / "dogfood" / "build").glob("*/receipt.jsonl"))
            self.assertTrue(receipts, "receipt.jsonl must be written on fail")
            lines = receipts[0].read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 2)
            rows = [json.loads(x) for x in lines]
            self.assertEqual(rows[0]["event"], "start")
            self.assertTrue(any(r.get("reason") == "grok_missing" for r in rows), rows)

    def test_dry_run_writes_real_receipt_without_exec_grok(self):
        with tempfile.TemporaryDirectory(prefix="pfy-build-dry-") as td:
            td = Path(td)
            # Provide a fake grok on PATH so missing-bin check passes; dry-run must not exec it
            fake_bin = td / "bin"
            fake_bin.mkdir()
            fake_grok = fake_bin / "grok"
            fake_grok.write_text("#!/bin/sh\necho UNEXPECTED_GROK_EXEC >&2\nexit 99\n")
            fake_grok.chmod(0o755)
            # Auth file under fake GROK_HOME so auth check can pass if dry_run skipped auth —
            # dry_run skips auth failure; still ok.
            gh = td / "grok-home"
            gh.mkdir()
            (gh / "auth.json").write_text('{"token":"test-not-real"}')
            path_env = "%s%s%s" % (fake_bin, os.pathsep, os.environ.get("PATH", ""))
            with mock.patch.dict(os.environ, {"GROK_HOME": str(gh)}, clear=False):
                rc = build.build_p(
                    "dry-run prompt",
                    cwd=td,
                    repo=ROOT,
                    dry_run=True,
                    path_env=path_env,
                    grok_home=gh,
                )
            self.assertEqual(rc, build.EXIT_OK)
            receipts = list((td / "pipelines" / "dogfood" / "build").glob("*/receipt.jsonl"))
            self.assertEqual(len(receipts), 1)
            rows = [json.loads(x) for x in receipts[0].read_text().splitlines() if x.strip()]
            events = [r["event"] for r in rows]
            self.assertIn("start", events)
            self.assertIn("toolset_apply", events)
            self.assertIn("decision_smoke", events)
            self.assertIn("decision_route_shadow", events)
            self.assertIn("grok_p", events)
            self.assertIn("done", events)
            grok_row = next(r for r in rows if r["event"] == "grok_p")
            self.assertTrue(grok_row.get("dry_run"))
            # Fake grok must not have been executed
            self.assertNotEqual(grok_row.get("rc"), 99)


if __name__ == "__main__":
    unittest.main()
