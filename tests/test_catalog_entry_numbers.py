"""catalog_check fails when two sources/entries files share an NNN prefix."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "catalog_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("catalog_check", CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
        self.assertEqual(_load().entry_number_collisions(), [])

    def test_duplicate_prefix_fails_with_both_names(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            entries = Path(tmp)
            (entries / "998-catalog-dup-a.md").write_text("# fixture\n", encoding="utf-8")
            (entries / "998-catalog-dup-b.md").write_text("# fixture\n", encoding="utf-8")
            problems = mod.entry_number_collisions(entries)
        self.assertEqual(
            problems,
            [
                "sources/entries number 998 is used by more than one file: "
                "998-catalog-dup-a.md, 998-catalog-dup-b.md"
            ],
        )


if __name__ == "__main__":
    unittest.main()
