"""_apply_mcp must not open a symlinked config.

is_file follows, so a mode-000 target still looks like a file and
read_bytes raises. A symlink has to be treated as absent: render from
empty, replace the directory entry, and do not back up the target.
A regular file still writes once and a second apply does not rewrite.
"""
from __future__ import annotations

import stat
import tempfile
import unittest
from pathlib import Path

from pfylib.setup import _apply_mcp

ROOT = Path(__file__).resolve().parents[1]
ENTRY = {"name": "demo", "command": "echo"}


def _op(path: Path) -> dict:
    return {"harness": "grok", "item": "demo", "path": path, "entry": ENTRY}


class ApplyMcpSymlinkTests(unittest.TestCase):
    def test_symlink_config_is_replaced_and_regular_file_does_not_rewrite(self) -> None:
        scratch = ROOT / "tmp" / "selfhost2-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="apply-mcp-", dir=scratch) as td:
            root = Path(td)
            plain = root / "plain.toml"
            records: list[dict] = []
            wrote, _changed = _apply_mcp(_op(plain), records)
            self.assertTrue(wrote)
            body = plain.read_bytes()
            self.assertIn(b"[mcp_servers.demo]", body)
            self.assertIn(b"echo", body)
            wrote_again, _changed_again = _apply_mcp(_op(plain), records)
            self.assertFalse(wrote_again)
            self.assertEqual(plain.read_bytes(), body)

            outside = root / "outside"
            outside.mkdir()
            secret = outside / "secret.toml"
            secret.write_bytes(b"secret-config\n")
            secret.chmod(0)
            link = root / "link.toml"
            link.symlink_to(secret)
            try:
                wrote, _changed = _apply_mcp(_op(link), records)
            finally:
                secret.chmod(stat.S_IRUSR | stat.S_IWUSR)
            self.assertTrue(wrote)
            self.assertFalse(link.is_symlink(), "config path is still a symlink")
            self.assertTrue(link.is_file())
            self.assertEqual(secret.read_bytes(), b"secret-config\n")
            self.assertFalse(Path(str(link) + ".pfy.backup").exists())
            rendered = link.read_bytes()
            self.assertIn(b"[mcp_servers.demo]", rendered)
            self.assertNotIn(b"secret-config", rendered)
            wrote_again, _changed_again = _apply_mcp(_op(link), records)
            self.assertFalse(wrote_again)
            self.assertEqual(link.read_bytes(), rendered)
            self.assertEqual(secret.read_bytes(), b"secret-config\n")


if __name__ == "__main__":
    unittest.main()
