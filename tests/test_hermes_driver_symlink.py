"""hermes_bot_driver must not write through a symlink.

A regular file still receives the new bytes. A symlink is replaced by a
regular file. The target's bytes stay as they were. A broken symlink becomes
a regular file instead of raising.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib import hermes_bot_driver  # noqa: E402


class HermesDriverSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-hermes-driver-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "real.json"
        target.write_text("keep", encoding="utf-8")
        link = self.tmp / "out.json"
        link.symlink_to(target.name)
        hermes_bot_driver._write(link, {"ok": False, "error": "closed"})
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")
        self.assertFalse(link.is_symlink())
        body = json.loads(link.read_text(encoding="utf-8"))
        self.assertIs(body["ok"], False)
        self.assertEqual(body["error"], "closed")

    def test_write_replaces_broken_symlink(self) -> None:
        link = self.tmp / "out.json"
        link.symlink_to("missing-target")
        hermes_bot_driver._write(link, {"ok": True, "error": None})
        self.assertFalse(link.is_symlink())
        body = json.loads(link.read_text(encoding="utf-8"))
        self.assertIs(body["ok"], True)

    def test_config_replaces_symlink_and_leaves_target(self) -> None:
        home = self.tmp / "home"
        home.mkdir()
        target = self.tmp / "real.yaml"
        target.write_text("keep-config", encoding="utf-8")
        link = home / "config.yaml"
        link.symlink_to(target)
        hermes_bot_driver._config(home, "probe-model", "http://127.0.0.1:9/v1", "off")
        self.assertEqual(target.read_text(encoding="utf-8"), "keep-config")
        self.assertFalse(link.is_symlink())
        text = link.read_text(encoding="utf-8")
        self.assertIn("probe-model", text)
        self.assertIn("http://127.0.0.1:9/v1", text)

    def test_regular_file_still_updates(self) -> None:
        path = self.tmp / "out.json"
        path.write_text("old", encoding="utf-8")
        hermes_bot_driver._write(path, {"ok": True, "error": None})
        self.assertFalse(path.is_symlink())
        body = json.loads(path.read_text(encoding="utf-8"))
        self.assertIs(body["ok"], True)
        self.assertNotIn("old", path.read_text(encoding="utf-8"))
