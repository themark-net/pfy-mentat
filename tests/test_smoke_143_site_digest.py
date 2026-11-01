"""taste fixtures_untouched must hash bytes and record symlinks without following them.

A symlink whose target bytes match the regular file is a different digest. An unreadable
target does not raise. _taste must use site_digest and must not call tree_hash.
"""
from __future__ import annotations

import importlib
import inspect
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


class SiteDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-site-digest-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_symlink_with_the_same_bytes_changes_the_digest(self) -> None:
        mod = load_smoke()
        site = self.tmp / "site"
        (site / "slop").mkdir(parents=True)
        page = site / "slop" / "index.html"
        page.write_text("<p>same</p>\n", encoding="utf-8")
        original = mod.site_digest(site)
        outside = self.tmp / "outside.html"
        outside.write_text("<p>same</p>\n", encoding="utf-8")
        page.unlink()
        page.symlink_to(outside)
        self.assertNotEqual(mod.site_digest(site), original)
        self.assertEqual(outside.read_text(encoding="utf-8"), "<p>same</p>\n")

    def test_unreadable_symlink_does_not_raise(self) -> None:
        mod = load_smoke()
        site = self.tmp / "site"
        (site / "slop").mkdir(parents=True)
        page = site / "slop" / "index.html"
        missing = self.tmp / "gone" / "index.html"
        page.symlink_to(missing)
        digest = mod.site_digest(site)
        self.assertIsInstance(digest, str)
        self.assertNotEqual(digest, "")
        self.assertFalse(missing.exists())

    def test_taste_uses_site_digest_and_not_tree_hash(self) -> None:
        mod = load_smoke()
        src = inspect.getsource(mod)
        self.assertIn("def site_digest", src)
        self.assertNotIn("tree_hash", src)
        taste = inspect.getsource(mod._taste)
        self.assertIn("site_digest", taste)
        self.assertIn('checks["fixtures_untouched"]', taste)
