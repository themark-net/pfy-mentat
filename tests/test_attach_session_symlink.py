"""Session reach must not follow a symlink.

write_session_reach replaces a symlink with a regular file and leaves the
target bytes. read_session_reach treats a symlink as absent. A regular file
still round-trips.
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


class AttachSessionSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-attach-session-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = self.tmp / "state"
        self.state.mkdir()
        prof = attach.profile("codex")
        self.assertIsNotNone(prof)
        self.name = prof["session_file"]

    def test_read_does_not_follow_symlink(self) -> None:
        target = self.tmp / "outside.txt"
        target.write_text("SECRET-SESSION\n", encoding="utf-8")
        link = self.state / self.name
        link.symlink_to(target)
        self.assertEqual(attach.read_session_reach("codex", self.state), "")
        self.assertEqual(target.read_text(encoding="utf-8"), "SECRET-SESSION\n")

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "outside.txt"
        target.write_text("SECRET-SESSION\n", encoding="utf-8")
        link = self.state / self.name
        link.symlink_to(target)
        attach.write_session_reach("codex", self.state, "ready-now")
        self.assertEqual(target.read_text(encoding="utf-8"), "SECRET-SESSION\n")
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), "ready-now\n")
        self.assertEqual(attach.read_session_reach("codex", self.state), "ready-now")

    def test_write_replaces_broken_symlink(self) -> None:
        link = self.state / self.name
        link.symlink_to("missing-session")
        attach.write_session_reach("codex", self.state, "recovered")
        self.assertFalse((self.state / "missing-session").exists())
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), "recovered\n")

    def test_regular_file_still_round_trips(self) -> None:
        attach.write_session_reach("codex", self.state, "plain-session")
        path = self.state / self.name
        self.assertFalse(path.is_symlink())
        self.assertEqual(attach.read_session_reach("codex", self.state), "plain-session")
