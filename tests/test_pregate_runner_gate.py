"""Pregate must not start while a GitHub runner worker is on this host.

Fail: a live process whose name matches the runner pattern still lets
pregate parse a bad ref (exit 2) and begin setup.
Recover: exit 3 and a not-starting message while that process is alive.
After it exits, the same command reaches the unknown-ref check (exit 2).
A short --wait-runner that expires stays at exit 3. A wait that outlasts
the process recovers to the unknown-ref check.
A shell that only quotes the name does not block.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREGATE = ROOT / "scripts" / "pregate.sh"

# prctl(PR_SET_NAME) then sleep. The child is reparented so init reaps it.
# A copied coreutils sleep exits at once under a foreign name, and pgrep -x
# still matches the zombie until the parent reaps it.
_SLEEPER = r"""
import ctypes
import os
import sys
import time

token, seconds, ready, pidfile = sys.argv[1:]
child = os.fork()
if child > 0:
    for _ in range(300):
        if os.path.exists(ready):
            os._exit(0)
        time.sleep(0.01)
    os._exit(1)
os.setsid()
libc = ctypes.CDLL(None)
libc.prctl.argtypes = [
    ctypes.c_int, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong
]
libc.prctl.restype = ctypes.c_int
if libc.prctl(15, token.encode(), 0, 0, 0) != 0:
    os._exit(2)
with open(pidfile, "w", encoding="ascii") as fh:
    fh.write(str(os.getpid()))
with open(ready, "w", encoding="ascii") as fh:
    fh.write("ok")
time.sleep(int(seconds))
"""


def _scratch() -> Path:
    path = ROOT / "tmp" / "pregate-runner-gate"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ppid(pid: int) -> int:
    for line in Path(f"/proc/{pid}/status").read_text().splitlines():
        if line.startswith("PPid:"):
            return int(line.split()[1])
    raise AssertionError(f"no PPid for {pid}")


def _pattern(token: str) -> str:
    # Bracket the last character so pgrep does not match its own argv.
    return token[:-1] + "[" + token[-1] + "]"


class _NamedSleeper:
    """Process name is the token. Init reaps it, so pgrep does not see a zombie."""

    def __init__(self, pid: int):
        self.pid = pid

    def _state(self) -> str | None:
        try:
            text = Path(f"/proc/{self.pid}/stat").read_text()
        except FileNotFoundError:
            return None
        end = text.rfind(")")
        if end < 0 or end + 2 >= len(text):
            return None
        return text[end + 2]

    def poll(self) -> int | None:
        state = self._state()
        if state is None or state == "Z":
            return 0
        return None

    def kill(self) -> None:
        try:
            os.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    def wait(self, timeout: float = 5) -> int:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.poll() is not None:
                return 0
            time.sleep(0.05)
        raise subprocess.TimeoutExpired(cmd=str(self.pid), timeout=timeout)


class PregateRunnerGateTests(unittest.TestCase):
    def _spawn(self, token: str, seconds: int) -> _NamedSleeper:
        # pgrep -x matches comm. exec -a does not change it, and a renamed
        # coreutils sleep refuses the foreign name and exits immediately.
        if len(token) > 15:
            raise AssertionError(f"comm is truncated at 15 chars: {token}")
        scratch = _scratch()
        ready = scratch / f"{token}.ready"
        pidfile = scratch / f"{token}.pid"
        ready.unlink(missing_ok=True)
        pidfile.unlink(missing_ok=True)
        proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _SLEEPER,
                token,
                str(seconds),
                str(ready),
                str(pidfile),
            ],
            cwd=scratch,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            rc = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            raise
        if rc != 0 or not pidfile.is_file():
            raise AssertionError(f"fake worker failed to start: rc={rc}")
        pid = int(pidfile.read_text(encoding="ascii").strip())
        sleeper = _NamedSleeper(pid)
        try:
            comm = Path(f"/proc/{pid}/comm").read_text().strip()
        except FileNotFoundError as exc:
            raise AssertionError(f"fake worker {pid} exited before the check") from exc
        if comm != token:
            sleeper.kill()
            sleeper.wait(timeout=5)
            raise AssertionError(f"comm is {comm!r}, want {token!r}")
        ppid = _ppid(pid)
        if ppid == os.getpid():
            sleeper.kill()
            sleeper.wait(timeout=5)
            raise AssertionError("fake worker is still our child; its zombie would keep matching pgrep")
        return sleeper

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
        token = "pfyfake" + uuid.uuid4().hex[:6]
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
        token = "pfyfake" + uuid.uuid4().hex[:6]
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

    def test_a_shell_that_only_quotes_the_name_does_not_block(self):
        # Fail: pgrep -f matches this shell and pregate exits 3, which is how
        # the image-pin tests failed in every discover while no worker ran.
        # Recover: the process name is bash, so the unknown-ref check runs.
        token = "pfyquote" + uuid.uuid4().hex[:4]
        pattern = _pattern(token)
        quoter = subprocess.Popen(
            ["bash", "-c", f"echo {token} >/dev/null; sleep 60"],
            cwd=_scratch(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(0.2)
            proc = self._run(pattern, "not-a-real-ref")
        finally:
            quoter.kill()
            quoter.wait(timeout=5)
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 2, blob)
        self.assertIn("unknown ref", proc.stderr)
        self.assertNotIn("not starting", proc.stderr)


if __name__ == "__main__":
    unittest.main()
