"""Spawn receipt must not follow a symlink.

_write_spawn_receipt replaces a symlink with a regular file and leaves the
target bytes. A regular file still receives the JSON receipt. A write error
is still swallowed.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import attach  # noqa: E402


class AttachReceiptSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-attach-receipt-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = self.tmp / "state"
        self.state.mkdir()

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "outside.json"
        target.write_text("SECRET\n", encoding="utf-8")
        link = self.state / "codex-attach-receipt.json"
        link.symlink_to(target)
        attach._write_spawn_receipt(self.state, "codex", 3)
        self.assertEqual(target.read_text(encoding="utf-8"), "SECRET\n")
        self.assertFalse(link.is_symlink())
        body = json.loads(link.read_text(encoding="utf-8"))
        self.assertEqual(body["exit_code"], 3)
        self.assertEqual(body["live"], "FAIL")

    def test_write_replaces_broken_symlink(self) -> None:
        link = self.state / "codex-attach-receipt.json"
        link.symlink_to("missing-receipt")
        attach._write_spawn_receipt(self.state, "codex", None)
        self.assertFalse((self.state / "missing-receipt").exists())
        self.assertFalse(link.is_symlink())
        body = json.loads(link.read_text(encoding="utf-8"))
        self.assertIsNone(body["exit_code"])

    def test_regular_file_still_receives_receipt(self) -> None:
        attach._write_spawn_receipt(self.state, "codex", 0)
        path = self.state / "codex-attach-receipt.json"
        self.assertFalse(path.is_symlink())
        body = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(body["exit_code"], 0)
        self.assertEqual(body["live"], "FAIL")

    def test_unwritable_directory_does_not_raise(self) -> None:
        blocked = self.tmp / "blocked"
        blocked.write_text("not-a-dir", encoding="utf-8")
        attach._write_spawn_receipt(blocked, "codex", 1)
        self.assertTrue(blocked.is_file())
        self.assertEqual(blocked.read_text(encoding="utf-8"), "not-a-dir")
