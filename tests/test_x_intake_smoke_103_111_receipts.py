"""Entries 103-111 write receipts under pipelines/smoke and leave that tree clean.

The skip path (tool not staged) is enough: each smoke still writes latest.json.
kolibri1/latest.json stays tracked. pipelines/smoke/ is not ignored as a whole.
"""
from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# script, entry. These are the dirs the 103-111 smokes pass to write().
ENTRIES = (
    ("examples/x-intake-local/smoke_103_105.py", "bugpatrol"),
    ("examples/x-intake-local/smoke_103_105.py", "graphjin"),
    ("examples/x-intake-local/smoke_103_105.py", "antislop"),
    ("examples/x-intake-local/smoke_106_108.py", "rulora"),
    ("examples/x-intake-local/smoke_106_108.py", "har"),
    ("examples/x-intake-local/smoke_106_108.py", "cassmemory"),
    ("examples/x-intake-local/smoke_109_111.py", "smolvm"),
    ("examples/x-intake-local/smoke_109_111.py", "brigade"),
    ("examples/x-intake-local/smoke_109_111.py", "runx"),
)

_BIN_KEYS = (
    "BUGPATROL_BIN", "BUGPATROL_NODE", "GRAPHJIN_BIN", "GRAPHJIN_SHA256", "ANTISLOP_DIR",
    "RULORA_DIR", "RULORA_NODE", "HAR_BIN", "HAR_NODE", "CM_BIN", "CM_SHA256",
    "SMOLVM_BIN", "SMOLVM_SHA256", "BRIGADE_BIN", "BRIGADE_VERSION",
    "RUNX_BIN", "RUNX_SHA256", "RUNX_SRC", "RUNX_NODE",
    "PFY_SMOKE_RECEIPT_DIR",
)


class XIntakeSmoke103111ReceiptTests(unittest.TestCase):
    def test_skip_path_receipts_are_ignored_and_kolibri_stays_tracked(self) -> None:
        # Fail: a 103-111 receipt shows up in git status, or kolibri1/latest.json is ignored.
        # Recover: each skip-path smoke writes latest.json, status for pipelines/smoke is empty,
        # and the kolibri receipt is still tracked.
        env = os.environ.copy()
        for key in _BIN_KEYS:
            env.pop(key, None)
        for script, entry in ENTRIES:
            proc = subprocess.run(
                ["python3", script, "--entry", entry],
                cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60,
            )
            blob = proc.stdout + proc.stderr
            self.assertNotIn("Traceback", proc.stderr, blob)
            self.assertEqual(proc.returncode, 2, blob)
            path = ROOT / "pipelines" / "smoke" / entry / "latest.json"
            self.assertTrue(path.is_file(), blob)
            receipt = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("verdict"), "FAIL_CANNOT_RUN_HERE", receipt)
        status = subprocess.run(
            ["git", "status", "--porcelain", "pipelines/smoke"],
            cwd=str(ROOT), capture_output=True, text=True, check=True,
        )
        self.assertEqual(status.stdout, "", status.stdout)
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "pipelines/smoke/kolibri1/latest.json"],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        self.assertEqual(tracked.returncode, 0, tracked.stderr)
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", "--", "pipelines/smoke/kolibri1/latest.json"],
            cwd=str(ROOT),
        )
        self.assertEqual(ignored.returncode, 1, "kolibri1/latest.json is ignored")


if __name__ == "__main__":
    unittest.main()
