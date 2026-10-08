"""catalog_check fails when two sources/entries files share an NNN prefix."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "catalog_check.py"
ENTRIES = ROOT / "sources" / "entries"


def _run_check() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )


class CatalogEntryNumberTests(unittest.TestCase):
    def test_real_tree_passes(self):
        proc = _run_check()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS catalog-check", proc.stdout)

    def test_duplicate_prefix_fails_with_both_names(self):
        first = ENTRIES / "998-catalog-dup-a.md"
        second = ENTRIES / "998-catalog-dup-b.md"
        first.write_text("# fixture\n", encoding="utf-8")
        second.write_text("# fixture\n", encoding="utf-8")
        try:
            proc = _run_check()
            text = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, text)
            self.assertIn("FAIL catalog-check", text)
            self.assertIn(
                "sources/entries number 998 is used by more than one file: "
                "998-catalog-dup-a.md, 998-catalog-dup-b.md",
                text,
            )
        finally:
            first.unlink(missing_ok=True)
            second.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
