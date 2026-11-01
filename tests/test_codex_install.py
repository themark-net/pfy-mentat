"""Codex installer is one registry line, shared by CLI stub and Attach (T-0105)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import attach, registry  # noqa: E402
from tests.support_missing_harness import run_missing_harness  # noqa: E402

INSTALL = "curl -fsSL https://chatgpt.com/codex/install.sh | sh"


class CodexInstallTests(unittest.TestCase):
    def test_registry_setup_and_attach_share_the_installer(self):
        row = next(h for h in registry.load_harnesses(ROOT)["harnesses"] if h["id"] == "codex")
        self.assertEqual(row["setup"], INSTALL)
        prof = attach.profile("codex", ROOT)
        self.assertEqual(prof["next_install"], INSTALL)

    def test_missing_binary_next_step_is_the_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = attach.open_session(
                "codex",
                ROOT=ROOT,
                STATE=Path(tmp),
                which_bin=lambda *a: "",
                live_openai_base=lambda: ("", {"engine": "none", "status": "missing"}),
                inspect_models=lambda b: [],
                record_sidecar_pid=lambda *a: None,
                record_last_verb=lambda *a: None,
                pid_alive=lambda p: False,
                root_dir=ROOT,
            )
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["next_step"], INSTALL)

    def test_missing_binary_prints_registry_installer_and_exits_2(self):
        """Fail: the missing codex arm prints another installer, exits 0, or runs curl.
        Recover: print the registry setup line and exit 2. Do not execute it."""
        proc = run_missing_harness("codex")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(INSTALL, proc.stdout)
        self.assertIn("FAIL attach -- codex missing", proc.stdout)


if __name__ == "__main__":
    unittest.main()
