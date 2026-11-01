"""Pregate must not start while a GitHub runner worker is on this host.

Fail: a fake process whose argv matches the runner pattern still lets
pregate parse a bad ref (exit 2) and begin setup.
Recover: exit 3 and a not-starting message while that process is alive.
After it exits, the same command reaches the unknown-ref check (exit 2).
A short --wait-runner that expires stays at exit 3. A wait that outlasts
the process recovers to the unknown-ref check.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREGATE = ROOT / "scripts" / "pregate.sh"


def _scratch() -> Path:
    path = ROOT / "tmp" / "pregate-runner-gate"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pattern(token: str) -> str:
    # Bracket the last character so pgrep does not match its own argv.
    return token[:-1] + "[" + token[-1] + "]"


class PregateRunnerGateTests(unittest.TestCase):
    def _spawn(self, token: str, seconds: int) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            ["bash", "-c", f"exec -a {token} sleep {seconds}"],
            cwd=_scratch(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _run(self, pattern: str, *args: str, poll: str = "1") -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PREGATE_RUNNER_PGREP"] = pattern
        env["PREGATE_RUNNER_POLL"] = poll
        env["TMPDIR"] = str(_scratch())
        return subprocess.run(
            ["bash", str(PREGATE), *args],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_fake_runner_blocks_then_a_dead_runner_reaches_the_ref_check(self):
        token = "pfy-fake-runner-" + uuid.uuid4().hex
        pattern = _pattern(token)
        proc = self._spawn(token, 60)
        try:
            time.sleep(0.2)
            blocked = self._run(pattern, "not-a-real-ref")
            blob = blocked.stdout + blocked.stderr
            self.assertEqual(blocked.returncode, 3, blob)
            self.assertIn("not starting", blocked.stderr)
            self.assertNotIn("unknown ref", blocked.stderr)
            self.assertNotIn("eval-structural", blob)
        finally:
            proc.kill()
            proc.wait(timeout=5)
        recovered = self._run(pattern, "not-a-real-ref")
        recovered_blob = recovered.stdout + recovered.stderr
        self.assertEqual(recovered.returncode, 2, recovered_blob)
        self.assertIn("unknown ref", recovered.stderr)

    def test_wait_runner_expires_then_a_longer_wait_recovers(self):
        token = "pfy-fake-runner-" + uuid.uuid4().hex
        pattern = _pattern(token)
        held = self._spawn(token, 60)
        try:
            time.sleep(0.2)
            expired = self._run(pattern, "--wait-runner", "1", "not-a-real-ref", poll="1")
            expired_blob = expired.stdout + expired.stderr
            self.assertEqual(expired.returncode, 3, expired_blob)
            self.assertIn("still running", expired.stderr)
        finally:
            held.kill()
            held.wait(timeout=5)
        short = self._spawn(token, 1)
        try:
            time.sleep(0.2)
            recovered = self._run(pattern, "--wait-runner", "8", "not-a-real-ref", poll="1")
        finally:
            if short.poll() is None:
                short.kill()
                short.wait(timeout=5)
        recovered_blob = recovered.stdout + recovered.stderr
        self.assertEqual(recovered.returncode, 2, recovered_blob)
        self.assertIn("unknown ref", recovered.stderr)
        self.assertNotIn("not starting", recovered.stderr)


if __name__ == "__main__":
    unittest.main()
