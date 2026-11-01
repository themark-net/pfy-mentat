"""Gemini installer is the registry setup line; start does not run it (T-0106)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import attach, registry  # noqa: E402
from tests.support_missing_harness import run_missing_harness  # noqa: E402

INSTALL = "npm install -g @google/gemini-cli"


class GeminiInstallTests(unittest.TestCase):
    def test_setup_is_the_installer_and_there_is_no_attach_profile(self):
        row = next(h for h in registry.load_harnesses(ROOT)["harnesses"] if h["id"] == "gemini")
        self.assertEqual(row["setup"], INSTALL)
        self.assertIsNone(row.get("attach"))
        self.assertIsNone(attach.profile("gemini", ROOT))

    def test_missing_binary_prints_registry_installer_and_exits_2(self):
        """Fail: the missing gemini arm prints another installer, exits 0, or runs npm.
        Recover: print the registry setup line and exit 2. Do not execute it."""
        proc = run_missing_harness("gemini")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(INSTALL, proc.stdout)
        self.assertIn("STUB harness: gemini", proc.stdout)


if __name__ == "__main__":
    unittest.main()
