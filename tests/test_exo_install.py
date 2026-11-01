"""Exo installer is the registry setup line; start does not run it (T-0107)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import attach, registry  # noqa: E402
from tests.support_missing_harness import run_missing_harness  # noqa: E402

INSTALL = (
    "curl -fsSL https://raw.githubusercontent.com/exoharness/exo/main/setup.sh -o setup.sh"
    " && bash setup.sh"
)


class ExoInstallTests(unittest.TestCase):
    def test_setup_is_the_installer_and_there_is_no_attach_profile(self):
        row = next(h for h in registry.load_harnesses(ROOT)["harnesses"] if h["id"] == "exo")
        self.assertEqual(row["setup"], INSTALL)
        self.assertIsNone(row.get("attach"))
        self.assertIsNone(attach.profile("exo", ROOT))
        self.assertEqual(registry.load_harnesses(ROOT).get("default_harness"), "grok")

    def test_missing_binary_prints_registry_installer_and_exits_2(self):
        """Fail: the missing exo arm prints another installer, exits 0, or runs setup.sh.
        Recover: print the registry setup line and exit 2. Do not create setup.sh."""
        proc = run_missing_harness("exo")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(INSTALL, proc.stdout)
        self.assertIn("STUB harness: exo", proc.stdout)
        self.assertFalse((ROOT / "setup.sh").exists())


if __name__ == "__main__":
    unittest.main()
