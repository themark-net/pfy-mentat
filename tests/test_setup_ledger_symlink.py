"""setup save_ledger must not open a symlinked ledger.

is_file follows, so a mode-000 target still looks like a file and
read_bytes raises. The matching-bytes check has to stay for a regular
file. A symlink has to be replaced without opening the target, and the
outside bytes have to stay.
"""
from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from pfylib.setup import ledger_path, save_ledger

ROOT = Path(__file__).resolve().parents[1]
ROW = {"backup": "", "harness": "grok", "item": "demo", "kind": "mcp", "path": "/cfg", "sha256_after": "abc"}


class SetupLedgerSymlinkTests(unittest.TestCase):
    def test_symlink_ledger_is_replaced_and_regular_file_stays_put(self) -> None:
        scratch = ROOT / "tmp" / "selfhost2-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        saved = os.environ.get("XDG_STATE_HOME")
        with tempfile.TemporaryDirectory(prefix="setup-ledger-", dir=scratch) as td:
            root = Path(td)
            try:
                regular = root / "regular-state"
                os.environ["XDG_STATE_HOME"] = str(regular)
                save_ledger([ROW])
                path = ledger_path()
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                first = path.stat()
                body = path.read_bytes()
                self.assertEqual(json.loads(body)["records"][0]["item"], "demo")
                save_ledger([ROW])
                second = path.stat()
                self.assertEqual(first.st_ino, second.st_ino)
                self.assertEqual(path.read_bytes(), body)

                state = root / "link-state"
                (state / "pfy").mkdir(parents=True)
                outside = root / "outside"
                outside.mkdir()
                secret = outside / "secret.json"
                secret.write_bytes(b"secret-bytes\n")
                secret.chmod(0)
                link = state / "pfy" / "installed.json"
                link.symlink_to(secret)
                os.environ["XDG_STATE_HOME"] = str(state)
                try:
                    save_ledger([ROW])
                finally:
                    secret.chmod(stat.S_IRUSR | stat.S_IWUSR)
                self.assertFalse(link.is_symlink(), "ledger path is still a symlink")
                self.assertTrue(link.is_file())
                self.assertEqual(secret.read_bytes(), b"secret-bytes\n")
                self.assertEqual(json.loads(link.read_text(encoding="utf-8"))["records"][0]["item"], "demo")
            finally:
                if saved is None:
                    os.environ.pop("XDG_STATE_HOME", None)
                else:
                    os.environ["XDG_STATE_HOME"] = saved


if __name__ == "__main__":
    unittest.main()
