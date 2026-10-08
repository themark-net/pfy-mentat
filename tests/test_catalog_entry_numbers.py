"""catalog_check.py fails when two sources/entries files share an NNN prefix."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "catalog_check.py"
DUP_MESSAGE = (
    "sources/entries number 998 is used by more than one file: "
    "998-catalog-dup-a.md, 998-catalog-dup-b.md"
)


def _run_check(entries_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(CHECK)]
    if entries_dir is not None:
        cmd.extend(["--entries-dir", str(entries_dir)])
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


class CatalogEntryNumberTests(unittest.TestCase):
    def test_real_tree_passes(self):
        proc = _run_check()
        text = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, text)
        self.assertIn("PASS catalog-check", proc.stdout)
        self.assertNotIn("used by more than one file", text)

    def test_duplicate_prefix_fails_with_both_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = Path(tmp)
            (entries / "998-catalog-dup-a.md").write_text("# fixture\n", encoding="utf-8")
            (entries / "998-catalog-dup-b.md").write_text("# fixture\n", encoding="utf-8")
            proc = _run_check(entries)
        text = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, text)
        self.assertIn("FAIL catalog-check", text)
        self.assertIn(DUP_MESSAGE, text)


if __name__ == "__main__":
    unittest.main()
