"""skill-up fixture_unchanged must hash bytes and record symlinks without following them.

A same-name symlink is not the same fixture as a regular file, even when the target bytes match.
A symlink whose target cannot be opened does not raise. The check in _skillup uses fixture_digest.
"""
from __future__ import annotations

import hashlib
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
    return importlib.import_module("smoke_146_147")


class FixtureDigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-fixture-digest-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _tree(self) -> Path:
        root = self.tmp / "skill"
        (root / "evals" / "cases").mkdir(parents=True)
        (root / "SKILL.md").write_text("skill-v1\n", encoding="utf-8")
        (root / "evals" / "eval.yaml").write_text("eval\n", encoding="utf-8")
        (root / "evals" / "cases" / "pass.yaml").write_text("pass\n", encoding="utf-8")
        (root / "evals" / "cases" / "fail.yaml").write_text("fail\n", encoding="utf-8")
        return root

    def test_byte_edit_and_symlink_change_the_digest(self) -> None:
        mod = load_smoke()
        root = self._tree()
        original = mod.fixture_digest(root)
        skill = root / "SKILL.md"
        skill.write_text("skill-v2\n", encoding="utf-8")
        self.assertNotEqual(mod.fixture_digest(root), original)
        skill.write_text("skill-v1\n", encoding="utf-8")
        self.assertEqual(mod.fixture_digest(root), original)

        outside = self.tmp / "outside.md"
        outside.write_text("skill-v1\n", encoding="utf-8")
        skill.unlink()
        skill.symlink_to(outside)
        self.assertNotEqual(mod.fixture_digest(root), original)
        self.assertEqual(outside.read_text(encoding="utf-8"), "skill-v1\n")
        digest = mod.fixture_digest(root)
        self.assertIsInstance(digest, str)
        self.assertNotEqual(digest, "")

    def test_unreadable_symlink_does_not_raise(self) -> None:
        mod = load_smoke()
        root = self._tree()
        missing = self.tmp / "missing-dir" / "nope.md"
        skill = root / "SKILL.md"
        skill.unlink()
        skill.symlink_to(missing)
        digest = mod.fixture_digest(root)
        self.assertIsInstance(digest, str)
        self.assertFalse(missing.exists())
        self.assertNotEqual(digest, hashlib.sha256(b"").hexdigest())

    def test_skillup_check_uses_fixture_digest(self) -> None:
        mod = load_smoke()
        src = inspect.getsource(mod._skillup)
        self.assertIn("fixture_digest", src)
        self.assertIn('checks["fixture_unchanged"]', src)
