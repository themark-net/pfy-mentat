"""Bake-off OpenCode config must not follow a symlink.

_write_config replaces opencode.json when it is a symlink and leaves the
target bytes. A regular file still receives the JSON. A broken symlink
becomes a regular file and does not create the missing target.
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

import opencode_arm  # noqa: E402


class OpenCodeArmSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-opencode-arm-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "cfg"
        self.home.mkdir()
        self.log = self.tmp / "mcp.log"
        self.task = "probe-task"

    def _write(self) -> None:
        opencode_arm._write_config(
            self.home, "probe-model", "http://127.0.0.1:9/v1", 1024, self.log, self.task
        )

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "real.json"
        target.write_text('{"keep": 1}\n', encoding="utf-8")
        dest_dir = self.home / "opencode"
        dest_dir.mkdir()
        link = dest_dir / "opencode.json"
        link.symlink_to(target)
        self._write()
        self.assertEqual(target.read_text(encoding="utf-8"), '{"keep": 1}\n')
        self.assertFalse(link.is_symlink())
        body = json.loads(link.read_text(encoding="utf-8"))
        self.assertEqual(body["model"], "ollama/probe-model")
        self.assertEqual(body["provider"]["ollama"]["options"]["baseURL"], "http://127.0.0.1:9/v1")

    def test_write_replaces_broken_symlink(self) -> None:
        dest_dir = self.home / "opencode"
        dest_dir.mkdir()
        link = dest_dir / "opencode.json"
        link.symlink_to("missing-opencode")
        self._write()
        self.assertFalse((dest_dir / "missing-opencode").exists())
        self.assertFalse(link.is_symlink())
        body = json.loads(link.read_text(encoding="utf-8"))
        self.assertEqual(body["model"], "ollama/probe-model")

    def test_regular_file_still_updates(self) -> None:
        self._write()
        path = self.home / "opencode" / "opencode.json"
        self.assertFalse(path.is_symlink())
        body = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(body["model"], "ollama/probe-model")
        path.write_text('{"old": true}\n', encoding="utf-8")
        self._write()
        body = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(body["model"], "ollama/probe-model")
        self.assertNotIn("old", body)
