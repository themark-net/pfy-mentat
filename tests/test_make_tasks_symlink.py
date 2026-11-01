"""Bake-off task writer must not follow a symlink.

main replaces OUT when it is a symlink and leaves the target bytes.
A regular file still receives the task JSON. A broken symlink becomes
a regular file and does not create the missing target.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAKE = ROOT / "examples" / "hermes-bakeoff"
if str(BAKE) not in sys.path:
    sys.path.insert(0, str(BAKE))

import make_tasks  # noqa: E402


class MakeTasksSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-make-tasks-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real_out = make_tasks.OUT
        self.addCleanup(self._restore_out)

    def _restore_out(self) -> None:
        make_tasks.OUT = self.real_out

    def _assert_payload(self, path: Path) -> None:
        self.assertFalse(path.is_symlink())
        body = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(body["schema_version"], "hermes-bakeoff.tasks.v0")
        self.assertEqual(body["n_tasks"], 27)
        self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "real.json"
        target.write_text("KEEP\n", encoding="utf-8")
        link = self.tmp / "tasks.json"
        link.symlink_to(target)
        make_tasks.OUT = link
        make_tasks.main()
        self.assertTrue(target.read_text(encoding="utf-8") == "KEEP\n")
        self._assert_payload(link)

    def test_write_replaces_broken_symlink(self) -> None:
        link = self.tmp / "tasks.json"
        link.symlink_to("missing-tasks")
        make_tasks.OUT = link
        make_tasks.main()
        self.assertFalse((self.tmp / "missing-tasks").exists())
        self._assert_payload(link)

    def test_regular_file_still_updates(self) -> None:
        path = self.tmp / "tasks.json"
        make_tasks.OUT = path
        make_tasks.main()
        self._assert_payload(path)
        path.write_text('{"old": true}\n', encoding="utf-8")
        make_tasks.main()
        body = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("old", body)
        self._assert_payload(path)
