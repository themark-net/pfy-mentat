"""backup_once must not open a symlink.

is_file follows, so a mode-000 target still looks like a file and
shutil.copy raises. A symlink returns no backup and stays put. A
regular file is copied once, and a later edit of that file does not
overwrite the first backup.
"""
from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from pfylib.adapters.base import backup_once

ROOT = Path(__file__).resolve().parents[1]


class BackupOnceSymlinkTests(unittest.TestCase):
    def test_symlink_is_skipped_and_regular_file_backs_up_once(self) -> None:
        scratch = ROOT / "tmp" / "selfhost2-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="backup-once-", dir=scratch) as td:
            root = Path(td)
            plain = root / "plain.toml"
            plain.write_bytes(b"version-one\n")
            dest = backup_once(plain)
            backup = Path(dest)
            self.assertEqual(backup, Path(str(plain) + ".pfy.backup"))
            self.assertEqual(backup.read_bytes(), b"version-one\n")
            plain.write_bytes(b"version-two\n")
            again = backup_once(plain)
            self.assertEqual(again, dest)
            self.assertEqual(backup.read_bytes(), b"version-one\n")
            self.assertEqual(plain.read_bytes(), b"version-two\n")

            outside = root / "outside"
            outside.mkdir()
            secret = outside / "secret.toml"
            secret.write_bytes(b"secret-backup\n")
            secret.chmod(0)
            link = root / "link.toml"
            link.symlink_to(secret)
            try:
                got = backup_once(link)
            finally:
                secret.chmod(stat.S_IRUSR | stat.S_IWUSR)
            self.assertEqual(got, "")
            self.assertFalse(Path(str(link) + ".pfy.backup").exists())
            self.assertTrue(link.is_symlink())
            self.assertEqual(os.readlink(link), str(secret))
            self.assertEqual(secret.read_bytes(), b"secret-backup\n")


if __name__ == "__main__":
    unittest.main()
