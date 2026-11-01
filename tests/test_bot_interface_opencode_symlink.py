"""write_opencode_config must not write through a symlink.

A symlink at opencode.json is replaced by a regular file. The target bytes stay.
A broken symlink does not create the missing target. A regular file still updates.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pfylib.bot_interface import write_opencode_config


class OpenCodeConfigSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-opencode-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.work = self.tmp / "work"
        self.work.mkdir()

    def _config(self) -> Path:
        return self.work / "opencode" / "config" / "opencode" / "opencode.json"

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        outside = self.tmp / "outside.json"
        outside.write_text("keep-outside\n", encoding="utf-8")
        path = self._config()
        path.parent.mkdir(parents=True)
        path.symlink_to(outside)
        written = write_opencode_config(self.work, "http://127.0.0.1:9/v1", "demo-model")
        self.assertEqual(written, path)
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep-outside\n")
        self.assertFalse(path.is_symlink())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "ollama/demo-model")

    def test_write_does_not_create_a_broken_symlink_target(self) -> None:
        path = self._config()
        path.parent.mkdir(parents=True)
        path.symlink_to("missing.json")
        missing = path.parent / "missing.json"
        write_opencode_config(self.work, "http://127.0.0.1:9/v1", "demo-model")
        self.assertFalse(missing.exists())
        self.assertFalse(path.is_symlink())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "ollama/demo-model")

    def test_regular_file_still_updates(self) -> None:
        path = write_opencode_config(self.work, "http://127.0.0.1:9/v1", "plain-model")
        self.assertFalse(path.is_symlink())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "ollama/plain-model")
        self.assertEqual(data["provider"]["ollama"]["options"]["baseURL"], "http://127.0.0.1:9/v1")
