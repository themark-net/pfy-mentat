"""loop_paint must not read or write loop-modules.json through a symlink.

load_selection treats a symlink as an empty selection and does not read the target.
save_selection replaces the symlink with a regular file. The target bytes stay.
A regular file still round-trips.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from pfylib import loop_paint


class LoopPaintSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-loop-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = self.tmp / "state"
        self.state.mkdir()
        self.saved = os.environ.get("PFY_STATE_DIR")
        os.environ["PFY_STATE_DIR"] = str(self.state)

    def tearDown(self) -> None:
        if self.saved is None:
            os.environ.pop("PFY_STATE_DIR", None)
        else:
            os.environ["PFY_STATE_DIR"] = self.saved

    def test_load_does_not_read_symlink_target(self) -> None:
        outside = self.tmp / "outside.json"
        outside.write_text(
            json.dumps({"enabled": ["keep-me"], "task": "hard"}) + "\n",
            encoding="utf-8",
        )
        link = self.state / "loop-modules.json"
        link.symlink_to(outside)
        loaded = loop_paint.load_selection(self.state)
        self.assertEqual(loaded["enabled"], [])
        self.assertEqual(loaded["task"], "interactive")
        self.assertEqual(json.loads(outside.read_text(encoding="utf-8"))["enabled"], ["keep-me"])

    def test_save_replaces_symlink_and_leaves_target(self) -> None:
        outside = self.tmp / "outside.json"
        outside.write_text('{"enabled":["keep-me"],"task":"hard"}\n', encoding="utf-8")
        link = self.state / "loop-modules.json"
        link.symlink_to(outside)
        loop_paint.save_selection({"enabled": ["jev"], "task": "bulk"}, self.state)
        self.assertEqual(outside.read_text(encoding="utf-8"), '{"enabled":["keep-me"],"task":"hard"}\n')
        self.assertFalse(link.is_symlink())
        saved = json.loads(link.read_text(encoding="utf-8"))
        self.assertEqual(saved["enabled"], ["jev"])
        self.assertEqual(saved["task"], "bulk")

    def test_save_does_not_create_a_broken_symlink_target(self) -> None:
        link = self.state / "loop-modules.json"
        link.symlink_to("missing.json")
        missing = self.state / "missing.json"
        loop_paint.save_selection({"enabled": ["jev"], "task": "interactive"}, self.state)
        self.assertFalse(missing.exists())
        self.assertFalse(link.is_symlink())
        saved = json.loads(link.read_text(encoding="utf-8"))
        self.assertEqual(saved["enabled"], ["jev"])

    def test_regular_file_still_round_trips(self) -> None:
        loop_paint.save_selection({"enabled": ["orchestration"], "task": "hard"}, self.state)
        path = self.state / "loop-modules.json"
        self.assertFalse(path.is_symlink())
        loaded = loop_paint.load_selection(self.state)
        self.assertEqual(loaded["enabled"], ["orchestration"])
        self.assertEqual(loaded["task"], "hard")
