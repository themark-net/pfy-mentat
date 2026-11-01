"""117 and 119 smoke tests must not write receipts into the repo.

Fail: test_wrong_kander_version_exits_2 or test_agentdescent_wrong_version_exits_2
creates or changes pipelines/smoke/<entry>/latest.json in this checkout.
Recover: both tests pass, and those paths are byte-for-byte what they were before.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    (
        "tests.test_x_intake_smoke_117_118.XIntakeSmoke117118Tests.test_wrong_kander_version_exits_2",
        ROOT / "pipelines/smoke/kander/latest.json",
    ),
    (
        "tests.test_x_intake_smoke_119_121.XIntakeSmoke119121Tests.test_agentdescent_wrong_version_exits_2",
        ROOT / "pipelines/smoke/agentdescent/latest.json",
    ),
)


def _bytes(path: Path):
    if not path.exists():
        return None
    return path.read_bytes()


class ReceiptsStayOutsideRepoTests(unittest.TestCase):
    def test_named_cases_pass_without_repo_receipts(self) -> None:
        before = {str(path): _bytes(path) for _name, path in CASES}
        for name, path in CASES:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", name],
                cwd=str(ROOT), capture_output=True, text=True, timeout=90,
            )
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, name + "\n" + blob)
            self.assertIn("OK", blob, blob)
            self.assertNotIn("skipped", blob.lower(), blob)
            self.assertEqual(_bytes(path), before[str(path)], "repo receipt changed: " + str(path))


if __name__ == "__main__":
    unittest.main()
