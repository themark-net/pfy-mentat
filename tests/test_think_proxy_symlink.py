"""Bake-off think-proxy log must not follow a symlink.

write_forced_log replaces the log path when it is a symlink and leaves
the target bytes. A regular file still receives the JSON lines. A broken
symlink becomes a regular file and does not create the missing target.
An empty row list still writes an empty regular file.
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

import think_proxy  # noqa: E402

LINE = '{"kind": "probe", "n": 1}\n'
ROWS = [{"n": 1, "kind": "probe"}]


class ThinkProxySymlinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pfy-think-proxy-symlink-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_write_replaces_symlink_and_leaves_target(self) -> None:
        target = self.tmp / "real.jsonl"
        target.write_text("KEEP\n", encoding="utf-8")
        parent = self.tmp / "logs"
        parent.mkdir()
        link = parent / "think-proxy.jsonl"
        link.symlink_to(target)
        think_proxy.write_forced_log(link, ROWS)
        self.assertEqual(target.read_text(encoding="utf-8"), "KEEP\n")
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), LINE)

    def test_write_replaces_broken_symlink(self) -> None:
        parent = self.tmp / "logs"
        parent.mkdir()
        link = parent / "think-proxy.jsonl"
        link.symlink_to("missing-think")
        think_proxy.write_forced_log(link, ROWS)
        self.assertFalse((parent / "missing-think").exists())
        self.assertFalse(link.is_symlink())
        self.assertEqual(link.read_text(encoding="utf-8"), LINE)

    def test_regular_file_still_updates(self) -> None:
        path = self.tmp / "logs" / "think-proxy.jsonl"
        think_proxy.write_forced_log(path, ROWS)
        self.assertFalse(path.is_symlink())
        self.assertEqual(path.read_text(encoding="utf-8"), LINE)
        path.write_text("OLD\n", encoding="utf-8")
        think_proxy.write_forced_log(path, ROWS)
        self.assertEqual(path.read_text(encoding="utf-8"), LINE)
        think_proxy.write_forced_log(path, [])
        self.assertFalse(path.is_symlink())
        self.assertEqual(path.read_text(encoding="utf-8"), "")
