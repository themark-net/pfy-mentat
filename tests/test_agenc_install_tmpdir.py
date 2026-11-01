"""bootstrap/agenc/install.sh keeps the Node tarball under TMPDIR.

An old node makes ensure_node choose a tarball path. A fake curl records -o and exits 1, so nothing is downloaded. A new enough node does not ask for a /tmp tarball.
"""
from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bootstrap" / "agenc" / "install.sh"

NODE = """#!/bin/bash
if [[ "${1:-}" == "-e" ]]; then
  printf '%s' "$AGENC_NODE_MAJOR"
  exit 0
fi
printf 'v%s.0.0\\n' "$AGENC_NODE_MAJOR"
"""

CURL = """#!/bin/bash
out=""
url=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o)
      out="$2"
      shift 2
      ;;
    -fsSL|-f|-s|-S|-L)
      shift
      ;;
    *)
      url="$1"
      shift
      ;;
  esac
done
{
  printf 'o %s\\n' "$out"
  printf 'url %s\\n' "$url"
} >> "$AGENC_CURL_LOG"
exit 1
"""


class AgencInstallTmpdirTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = ROOT / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="pfy-agenc-install-", dir=str(scratch))
        self.base = Path(self._td.name)
        self.home = self.base / "home"
        self.tmpdir = self.base / "tmpdir"
        self.home.mkdir()
        self.tmpdir.mkdir()
        bindir = self.home / "bin"
        bindir.mkdir()
        self._write_exe(bindir / "node", NODE)
        self._write_exe(bindir / "curl", CURL)
        self.curl_log = self.base / "curl.log"

    def tearDown(self) -> None:
        self._td.cleanup()

    def _write_exe(self, path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def run_install(self, major: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("AGENC_"):
                env.pop(key, None)
        env["HOME"] = str(self.home)
        env["TMPDIR"] = str(self.tmpdir)
        env["PATH"] = f"{self.home / 'bin'}:/usr/bin:/bin"
        env["AGENC_NODE_MAJOR"] = major
        env["AGENC_CURL_LOG"] = str(self.curl_log)
        return subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=str(self.base),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def curl_lines(self) -> list[str]:
        self.assertTrue(self.curl_log.is_file(), "curl was not called")
        return [line.strip() for line in self.curl_log.read_text(encoding="utf-8").splitlines()]

    def test_old_node_tarball_stays_under_tmpdir(self) -> None:
        proc = self.run_install("18")
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        outs = [line[2:] for line in self.curl_lines() if line.startswith("o ")]
        self.assertTrue(outs, self.curl_lines())
        for path in outs:
            self.assertTrue(path.startswith(str(self.tmpdir) + "/"), path)
            self.assertTrue(path.endswith(".tar.xz"), path)
            self.assertFalse(path.startswith("/tmp/"), path)
        self.assertNotIn("Traceback", proc.stderr)

    def test_new_node_does_not_request_a_tmp_tarball(self) -> None:
        proc = self.run_install("25")
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for line in self.curl_lines():
            if line.startswith("o ") and line[2:]:
                self.assertFalse(line[2:].startswith("/tmp/"), line)
        joined = "\n".join(self.curl_lines())
        self.assertNotIn("/tmp/", joined)


if __name__ == "__main__":
    unittest.main()
