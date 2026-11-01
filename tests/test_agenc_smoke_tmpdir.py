"""bootstrap/agenc/smoke.sh keeps the optional LLM tee under TMPDIR.

A PONG answer exits 0 and the log is inside TMPDIR. A non-PONG answer exits 1 and the failure text names that same path. The run does not write /tmp/agenc-smoke-llm.txt.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "bootstrap" / "agenc" / "smoke.sh"
LAUNCHER = ROOT / "bootstrap" / "agenc" / "agenc-launch"
FORBIDDEN = "/tmp/agenc-smoke-llm.txt"

AGENC = """#!/bin/bash
case "${1:-}" in
  --help|help|doctor|onboard) exit 0 ;;
  daemon) exit 0 ;;
  *) printf '%s\\n' "$AGENC_ANSWER" ;;
esac
"""

TEE = """#!/bin/bash
printf '%s\\n' "$1" > "$AGENC_TEE_ARGS"
if [[ "$1" == "$AGENC_TEE_ALLOWED"* ]]; then
  mkdir -p "$(dirname "$1")"
  /usr/bin/tee "$1"
else
  /usr/bin/tee "$AGENC_TEE_CAPTURE"
fi
"""


class AgencSmokeTmpdirTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = ROOT / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="pfy-agenc-smoke-", dir=str(scratch))
        self.base = Path(self._td.name)
        self.home = self.base / "home"
        self.tmpdir = self.base / "tmpdir"
        self.repo = self.base / "repo"
        self.home.mkdir()
        self.tmpdir.mkdir()
        bindir = self.home / ".local" / "bin"
        bindir.mkdir(parents=True)
        self._write_exe(bindir / "agenc", AGENC)
        self._write_exe(bindir / "tee", TEE)
        script_dir = self.repo / "bootstrap" / "agenc"
        script_dir.mkdir(parents=True)
        shutil.copy(SMOKE, script_dir / "smoke.sh")
        shutil.copy(LAUNCHER, script_dir / "agenc-launch")
        os.chmod(script_dir / "agenc-launch", 0o755)
        self.tee_args = self.base / "tee-args"
        self.capture = self.base / "capture.txt"

    def tearDown(self) -> None:
        self._td.cleanup()

    def _write_exe(self, path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def run_smoke(self, answer: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("AGENC_"):
                env.pop(key, None)
        env["HOME"] = str(self.home)
        env["TMPDIR"] = str(self.tmpdir)
        env["PATH"] = f"{self.home / '.local' / 'bin'}:/usr/bin:/bin"
        env["AGENC_SMOKE_LLM"] = "1"
        env["AGENC_ANSWER"] = answer
        env["AGENC_TEE_ARGS"] = str(self.tee_args)
        env["AGENC_TEE_ALLOWED"] = str(self.tmpdir)
        env["AGENC_TEE_CAPTURE"] = str(self.capture)
        return subprocess.run(
            ["bash", str(self.repo / "bootstrap" / "agenc" / "smoke.sh")],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_pong_log_stays_under_tmpdir(self) -> None:
        proc = self.run_smoke("PONG")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        recorded = self.tee_args.read_text(encoding="utf-8").strip()
        self.assertTrue(recorded.startswith(str(self.tmpdir) + "/"), recorded)
        self.assertNotEqual(recorded, FORBIDDEN)
        log = Path(recorded)
        self.assertTrue(log.is_file(), recorded)
        self.assertIn("pong", log.read_text(encoding="utf-8").lower())
        self.assertFalse(Path(FORBIDDEN).exists())

    def test_non_pong_exits_1_and_names_the_tmpdir_log(self) -> None:
        proc = self.run_smoke("NOPE")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        recorded = self.tee_args.read_text(encoding="utf-8").strip()
        self.assertTrue(recorded.startswith(str(self.tmpdir) + "/"), recorded)
        text = proc.stdout + proc.stderr
        self.assertIn(recorded, text)
        self.assertNotIn(FORBIDDEN, text)
        self.assertFalse(Path(FORBIDDEN).exists())


if __name__ == "__main__":
    unittest.main()
