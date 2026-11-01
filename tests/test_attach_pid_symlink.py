"""Terminal pid must not follow a symlink.

write_terminal_pid replaces a symlink with a regular file and leaves the
target bytes. read_terminal_pid treats a symlink as absent and returns 0.
A regular file still round-trips, and a non-integer regular file still
returns 0.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import attach  # noqa: E402


class AttachPidSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-attach-pid-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = self.tmp / "state"
        self.state.mkdir()
        prof = attach.profile("codex")
        self.assertIsNotNone(prof)
        self.name = prof["terminal_pid_file"]

    def test_read_does_not_follow_symlink(self) -> None:
        target = self.tmp / "outside.pid"
        target.write_text("99999\n", encoding="utf-8")
        link = self.state / self.name
        link.symlink_to(target)
        self.assertEqual(attach.read_terminal_pid("codex", self.state), 0)
        self.assertEqual(target.read_text(encoding="utf-8"), "99999\n")

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "outside.pid"
        target.write_text("99999\n", encoding="utf-8")
        link = self.state / self.name
        link.symlink_to(target)
        attach.write_terminal_pid("codex", self.state, 4242)
        self.assertEqual(target.read_text(encoding="utf-8"), "99999\n")
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), "4242\n")
        self.assertEqual(attach.read_terminal_pid("codex", self.state), 4242)

    def test_write_replaces_broken_symlink(self) -> None:
        link = self.state / self.name
        link.symlink_to("missing-pid")
        attach.write_terminal_pid("codex", self.state, 7)
        self.assertFalse((self.state / "missing-pid").exists())
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), "7\n")

    def test_regular_file_round_trips_and_bad_text_returns_zero(self) -> None:
        attach.write_terminal_pid("codex", self.state, 12)
        path = self.state / self.name
        self.assertFalse(path.is_symlink())
        self.assertEqual(attach.read_terminal_pid("codex", self.state), 12)
        path.write_text("nope\n", encoding="utf-8")
        self.assertEqual(attach.read_terminal_pid("codex", self.state), 0)
