"""tree_sig must follow the content hash in smoke_122_124.py.

Fail: an mtime-only touch changes the signature, or a same-size edit that
restores mtime does not. An unreadable file must be recorded: opening it
fails, and making it readable again changes the signature.
Recover: the signature ignores mtime, sees the byte change, and uses the
unreadable marker until the file can be read.
"""
from __future__ import annotations

import importlib.util
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    "smoke_112_114.py",
    "smoke_115_116.py",
    "smoke_117_118.py",
    "smoke_119_121.py",
)


def _load(filename: str):
    local = ROOT / "examples" / "x-intake-local"
    if str(local) not in sys.path:
        sys.path.insert(0, str(local))
    spec = importlib.util.spec_from_file_location("tree_sig_" + filename[:-3], local / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module.tree_sig


class TreeSigContentTests(unittest.TestCase):
    def test_content_not_mtime_and_unreadable_is_recorded(self) -> None:
        for filename in MODULES:
            tree_sig = _load(filename)
            with self.subTest(module=filename):
                self.assertIsNone(tree_sig(Path("/this/path/is/not/on/disk/pfy-tree-sig")))
                with tempfile.TemporaryDirectory(prefix="pfy-tree-sig-") as td:
                    root = Path(td)
                    target = root / "note.txt"
                    target.write_text("hello", encoding="utf-8")
                    before = tree_sig(root)
                    stamp = target.stat().st_mtime_ns
                    os.utime(target, ns=(stamp + 10**9, stamp + 10**9))
                    self.assertEqual(tree_sig(root), before, filename + " mtime-only touch")
                    target.write_text("hellp", encoding="utf-8")
                    os.utime(target, ns=(stamp, stamp))
                    self.assertNotEqual(tree_sig(root), before, filename + " same-size edit")
                    blocked = root / "blocked.txt"
                    blocked.write_text("secret", encoding="utf-8")
                    blocked.chmod(0)
                    try:
                        signed = tree_sig(root)
                        self.assertIsNotNone(signed)
                        blocked.chmod(stat.S_IRUSR | stat.S_IWUSR)
                        self.assertNotEqual(tree_sig(root), signed, filename + " unreadable marker")
                    finally:
                        blocked.chmod(stat.S_IRUSR | stat.S_IWUSR)


if __name__ == "__main__":
    unittest.main()
