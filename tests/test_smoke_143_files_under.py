"""files_under must not list a symlink as a file.

A symlink is omitted. Its target bytes stay. A regular file in the same directory is still listed.
"""
from __future__ import annotations

import importlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "examples" / "x-intake-local"


def load_smoke():
    if str(SMOKE_DIR) not in sys.path:
        sys.path.insert(0, str(SMOKE_DIR))
    return importlib.import_module("smoke_143_145")


class FilesUnderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-files-under-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_symlink_is_not_listed_and_target_stays(self) -> None:
        mod = load_smoke()
        root = self.tmp / "out"
        root.mkdir()
        (root / "real.txt").write_text("a\n", encoding="utf-8")
        outside = self.tmp / "outside.jpg"
        outside.write_text("jpeg\n", encoding="utf-8")
        link = root / "shot.jpg"
        link.symlink_to(outside)
        names = mod.files_under(root)
        self.assertEqual(names, ["real.txt"])
        self.assertTrue(link.is_symlink())
        self.assertEqual(outside.read_text(encoding="utf-8"), "jpeg\n")
