"""smoke_146 hiroute exits 2 before the entry when HIROUTE_TERM_WAIT is set and is not in range.

Unset, empty, or whitespace-only still reaches the HiRoute staging miss. A finite value in (0, 600] does too.
A bad value names HIROUTE_TERM_WAIT and is not reported as files not staged.
skill-up does not consult HIROUTE_TERM_WAIT.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "examples/x-intake-local/smoke_146_147.py"
NOT_STAGED = "not staged"
SKILLUP_MISS = "skill-up not found"


class TermWaitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="pfy-smoke146-term-")
        self.base = Path(self._td.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.path = self.base / "path"
        self.path.mkdir()
        self.receipts = self.base / "receipts"
        self.receipts.mkdir()

    def tearDown(self) -> None:
        self._td.cleanup()

    def run_entry(self, entry: str, term_wait: str | None) -> tuple[int, dict]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith(("HIROUTE_", "SKILLUP_", "PFY_XINTAKE_")) or key in ("PFY_SMOKE_RECEIPT_DIR",):
                env.pop(key, None)
        env["HOME"] = str(self.home)
        env["PATH"] = str(self.path)
        env["PFY_SMOKE_RECEIPT_DIR"] = str(self.receipts)
        if term_wait is not None:
            env["HIROUTE_TERM_WAIT"] = term_wait
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--entry", entry],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)
        receipt_path = self.receipts / entry / "latest.json"
        self.assertTrue(receipt_path.is_file(), proc.stdout + proc.stderr)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["exit_code"], proc.returncode)
        return proc.returncode, receipt

    def test_bad_term_wait_exits_2_before_staging(self) -> None:
        for bad in ("abc", "0", "-1", "nan", "inf", "601", "  "):
            with self.subTest(term_wait=bad):
                code, receipt = self.run_entry("hiroute", bad)
                reason = receipt["reason"]
                if bad.strip() == "":
                    self.assertEqual(code, 2, receipt)
                    self.assertIn(NOT_STAGED, reason)
                    self.assertNotIn("HIROUTE_TERM_WAIT", reason)
                    continue
                self.assertEqual(code, 2, receipt)
                self.assertIn("HIROUTE_TERM_WAIT", reason)
                self.assertNotIn(NOT_STAGED, reason)
                self.assertNotIn("checks", receipt)

    def test_unset_empty_or_in_range_still_reports_not_staged(self) -> None:
        for value in (None, "", "10", "600", "  10  "):
            with self.subTest(term_wait=value):
                code, receipt = self.run_entry("hiroute", value)
                self.assertEqual(code, 2, receipt)
                self.assertIn(NOT_STAGED, receipt["reason"])
                self.assertNotIn("HIROUTE_TERM_WAIT", receipt["reason"])

    def test_skill_up_ignores_bad_hiroute_term_wait(self) -> None:
        code, receipt = self.run_entry("skill-up", "abc")
        self.assertEqual(code, 2, receipt)
        self.assertIn(SKILLUP_MISS, receipt["reason"])
        self.assertNotIn("HIROUTE_TERM_WAIT", receipt["reason"])
