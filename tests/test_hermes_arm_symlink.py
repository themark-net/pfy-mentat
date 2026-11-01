"""Bake-off Hermes config must not follow a symlink.

_write_config replaces config.yaml when it is a symlink and leaves the
target bytes. A regular file still receives the yaml. A broken symlink
becomes a regular file and does not create the missing target.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAKE = ROOT / "examples" / "hermes-bakeoff"
if str(BAKE) not in sys.path:
    sys.path.insert(0, str(BAKE))

import hermes_arm  # noqa: E402


class HermesArmSymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-hermes-arm-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.log = self.tmp / "mcp.log"
        self.task = "probe-task"

    def _write(self, home: Path) -> None:
        hermes_arm._write_config(
            home, "probe-model", "http://127.0.0.1:9/v1", 1024, self.log, self.task
        )

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "real.yaml"
        target.write_text("keep-config", encoding="utf-8")
        link = self.home / "config.yaml"
        link.symlink_to(target)
        self._write(self.home)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep-config")
        self.assertFalse(link.is_symlink())
        text = link.read_text(encoding="utf-8")
        self.assertIn("probe-model", text)
        self.assertIn("http://127.0.0.1:9/v1", text)

    def test_write_replaces_broken_symlink(self) -> None:
        link = self.home / "config.yaml"
        link.symlink_to("missing-config")
        self._write(self.home)
        self.assertFalse((self.home / "missing-config").exists())
        self.assertFalse(link.is_symlink())
        self.assertIn("probe-model", link.read_text(encoding="utf-8"))

    def test_regular_file_still_updates(self) -> None:
        path = self.home / "config.yaml"
        path.write_text("old", encoding="utf-8")
        self._write(self.home)
        self.assertFalse(path.is_symlink())
        text = path.read_text(encoding="utf-8")
        self.assertIn("probe-model", text)
        self.assertNotIn("old", text)
