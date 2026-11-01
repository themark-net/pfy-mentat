"""Pregate must not start while a GitHub runner worker is on this host.

Fail: a fake process whose name matches the runner name still lets
pregate parse a bad ref (exit 2) and begin setup. Or a shell whose argv
only mentions the name blocks pregate (the pgrep -f self-match loop).
Recover: exit 3 and a not-starting message while that process is alive.
After it exits, the same command reaches the unknown-ref check (exit 2).
A short --wait-runner that expires stays at exit 3. A wait that outlasts
the process recovers to the unknown-ref check.
"""
from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import threading
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


def _token() -> str:
    # pgrep -x compares the 15-char process name, so keep it short.
    return "pfyrw" + uuid.uuid4().hex[:8]


def _fake_exe(token: str) -> Path:
    # For a #! script the kernel names the process after the script file,
    # so a script called <token> runs as <token>. A symlink to sleep does
    # not work with multicall coreutils.
    exe = _scratch() / token
    if not exe.exists():
        exe.write_text('#!/bin/sh\nsleep "$1"\n')
        exe.chmod(0o755)
    return exe


def _visible(token: str) -> bool:
    return subprocess.run(["pgrep", "-x", token], capture_output=True).returncode == 0


class PregateRunnerGateTests(unittest.TestCase):
    def _spawn(self, token: str, seconds: int) -> subprocess.Popen[bytes]:
        proc = subprocess.Popen(
            [str(_fake_exe(token)), str(seconds)],
            cwd=_scratch(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        # Reap it as soon as it exits. An unreaped zombie keeps its name
        # and pgrep -x would still see a runner.
        threading.Thread(target=proc.wait, daemon=True).start()
        return proc

    def _stop(self, proc: subprocess.Popen[bytes]) -> None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)

    def _run(self, pattern: str, *args: str, poll: str = "1") -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PREGATE_RUNNER_NAME"] = pattern
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
        token = _token()
        pattern = token
        proc = self._spawn(token, 60)
        try:
            time.sleep(0.2)
            self.assertTrue(_visible(token), "fake runner not visible to pgrep -x")
            blocked = self._run(pattern, "not-a-real-ref")
            blob = blocked.stdout + blocked.stderr
            self.assertEqual(blocked.returncode, 3, blob)
            self.assertIn("not starting", blocked.stderr)
            self.assertNotIn("unknown ref", blocked.stderr)
            self.assertNotIn("eval-structural", blob)
        finally:
            self._stop(proc)
        recovered = self._run(pattern, "not-a-real-ref")
        recovered_blob = recovered.stdout + recovered.stderr
        self.assertEqual(recovered.returncode, 2, recovered_blob)
        self.assertIn("unknown ref", recovered.stderr)

    def test_wait_runner_expires_then_a_longer_wait_recovers(self):
        token = _token()
        pattern = token
        held = self._spawn(token, 60)
        try:
            time.sleep(0.2)
            self.assertTrue(_visible(token), "fake runner not visible to pgrep -x")
            expired = self._run(pattern, "--wait-runner", "1", "not-a-real-ref", poll="1")
            expired_blob = expired.stdout + expired.stderr
            self.assertEqual(expired.returncode, 3, expired_blob)
            self.assertIn("still running", expired.stderr)
        finally:
            self._stop(held)
        short = self._spawn(token, 1)
        try:
            time.sleep(0.2)
            recovered = self._run(pattern, "--wait-runner", "8", "not-a-real-ref", poll="1")
        finally:
            self._stop(short)
        recovered_blob = recovered.stdout + recovered.stderr
        self.assertEqual(recovered.returncode, 2, recovered_blob)
        self.assertIn("unknown ref", recovered.stderr)
        self.assertNotIn("not starting", recovered.stderr)

    def test_a_shell_that_only_mentions_the_name_does_not_block(self):
        token = _token()
        # argv carries the name, the process name is bash. pgrep -f would
        # match this and refuse forever. pgrep -x must not.
        mention = subprocess.Popen(
            ["bash", "-c", f"sleep 60; echo {token}"],
            cwd=_scratch(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(0.2)
            self.assertFalse(_visible(token))
            res = self._run(token, "not-a-real-ref")
        finally:
            mention.kill()
            mention.wait(timeout=5)
        blob = res.stdout + res.stderr
        self.assertEqual(res.returncode, 2, blob)
        self.assertIn("unknown ref", res.stderr)
        self.assertNotIn("not starting", res.stderr)


if __name__ == "__main__":
    unittest.main()
