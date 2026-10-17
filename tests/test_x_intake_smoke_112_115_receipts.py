"""Running the 112-114 and 115-116 smoke tests must not touch pipelines/smoke.

git status lists an ignored directory, so a rewrite of latest.json does not change that
text. The snapshot also records size and mtime of every file under pipelines/smoke.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    "tests.test_x_intake_smoke_112_114",
    "tests.test_x_intake_smoke_115_116",
)


def _snapshot() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--ignored", "--", "pipelines/smoke"],
        cwd=str(ROOT), capture_output=True, text=True, check=True,
    ).stdout
    lines = [status.rstrip("\n")]
    root = ROOT / "pipelines" / "smoke"
    if root.is_dir():
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            st = path.stat()
            lines.append(f"{path.relative_to(ROOT)} {st.st_size} {st.st_mtime_ns}")
    return "\n".join(lines) + "\n"


class XIntakeSmoke112115ReceiptTests(unittest.TestCase):
    def test_both_modules_leave_pipelines_smoke_unchanged(self) -> None:
        # Fail: a 112 or 115 test writes pipelines/smoke/<entry>/latest.json in the repo.
        # Recover: every smoke run sets PFY_SMOKE_RECEIPT_DIR to a temp dir and reads it there.
        before = _snapshot()
        ran = []
        for module in MODULES:
            ran.append(subprocess.run(
                [sys.executable, "-m", "unittest", module],
                cwd=str(ROOT), capture_output=True, text=True, timeout=180,
            ))
        after = _snapshot()
        self.assertEqual(before, after)
        for proc in ran:
            self.assertEqual(proc.returncode, 0, proc.stdout[-400:] + proc.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
