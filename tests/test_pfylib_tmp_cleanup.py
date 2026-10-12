"""A run of the mkdtemp modules leaves no new /tmp/pfylib-* directory."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULES = (
    "tests.test_cli",
    "tests.test_toolsets",
    "tests.test_hedge",
    "tests.test_loop_paint",
    "tests.test_attach",
)


def _pfylib_tmp_paths() -> set[str]:
    return {str(p) for p in Path("/tmp").glob("pfylib-*")}


class PfylibTmpCleanupTests(unittest.TestCase):
    def test_module_run_leaves_no_new_pfylib_tmp_dirs(self):
        before = _pfylib_tmp_paths()
        proc = subprocess.run(
            ["python3", "-m", "unittest", *MODULES],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        after = _pfylib_tmp_paths()
        self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
        self.assertEqual(after - before, set())
