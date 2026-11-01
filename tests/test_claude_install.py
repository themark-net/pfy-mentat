"""Claude installer is one registry line, shared by CLI stub and Attach (T-0104)."""
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

INSTALL = "curl -fsSL https://claude.ai/install.sh | bash"


class ClaudeInstallTests(unittest.TestCase):
    def test_registry_setup_and_attach_share_the_installer(self):
        row = next(h for h in registry.load_harnesses(ROOT)["harnesses"] if h["id"] == "claude-code")
        self.assertEqual(row["setup"], INSTALL)
        prof = attach.profile("claude-code", ROOT)
        self.assertEqual(prof["next_install"], INSTALL)

    def test_missing_binary_next_step_is_the_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = attach.open_session(
                "claude",
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
        """Fail: the missing claude arm prints another installer, exits 0, or runs curl.
        Recover: print the registry setup line and exit 2. Do not execute it."""
        proc = run_missing_harness("claude")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(INSTALL, proc.stdout)
        self.assertIn("FAIL attach -- claude missing", proc.stdout)


if __name__ == "__main__":
    unittest.main()
