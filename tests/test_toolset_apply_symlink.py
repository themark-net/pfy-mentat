"""toolsets.apply must not write through a symlink inside an allowed root.

A regular file still updates in place. A symlink is replaced by a regular file.
The target's bytes stay as they were. Outside the root, a symlink is still refused
and its target stays untouched.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from pfylib import toolsets


class ApplySymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-toolset-symlink-"))
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

    def _apply(self, path: Path, mode: str, **extra) -> dict:
        spec = {"path": str(path), "mode": mode}
        spec.update(extra)
        plan = {
            "ok": True,
            "toolset": "jev",
            "harness": "codex",
            "copy": "symlink probe",
            "files": [spec],
        }
        return toolsets.apply(plan, yes=True, state=self.state)

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.state / "real.txt"
        target.write_text("keep", encoding="utf-8")
        link = self.state / "link.txt"
        link.symlink_to("real.txt")
        out = self._apply(link, "write", content="new\n")
        self.assertTrue(out["ok"], out)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), "new\n")

    def test_append_marker_does_not_read_or_write_through_symlink(self) -> None:
        target = self.state / "real.md"
        target.write_text("keep-body\n", encoding="utf-8")
        link = self.state / "link.md"
        link.symlink_to("real.md")
        out = self._apply(link, "append-marker", content="block")
        self.assertTrue(out["ok"], out)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep-body\n")
        self.assertFalse(link.is_symlink())
        text = link.read_text(encoding="utf-8")
        self.assertIn("block", text)
        self.assertNotIn("keep-body", text)

    def test_json_merge_does_not_read_or_write_through_symlink(self) -> None:
        target = self.state / "real.json"
        target.write_text(json.dumps({"keep": 1}) + "\n", encoding="utf-8")
        link = self.state / "link.json"
        link.symlink_to("real.json")
        out = self._apply(link, "json-merge", fragment={"added": 2})
        self.assertTrue(out["ok"], out)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"keep": 1})
        self.assertFalse(link.is_symlink())
        merged = json.loads(link.read_text(encoding="utf-8"))
        self.assertEqual(merged.get("added"), 2)
        self.assertNotIn("keep", merged)

    def test_regular_file_still_updates_in_place(self) -> None:
        path = self.state / "plain.txt"
        path.write_text("old", encoding="utf-8")
        out = self._apply(path, "write", content="new\n")
        self.assertTrue(out["ok"], out)
        self.assertFalse(path.is_symlink())
        self.assertEqual(path.read_text(encoding="utf-8"), "new\n")

    def test_symlink_to_outside_target_is_not_modified(self) -> None:
        outside = self.tmp / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        link = self.state / "escape.txt"
        link.symlink_to(outside)
        out = self._apply(link, "write", content="pwned\n")
        self.assertEqual(outside.read_text(encoding="utf-8"), "secret")
        if out["ok"]:
            self.assertFalse(link.is_symlink())
            self.assertEqual(link.read_text(encoding="utf-8"), "pwned\n")
        else:
            self.assertTrue(any("refused" in f["result"] for f in out["failed"]))
