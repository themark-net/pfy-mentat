"""Entries 098-100 smokes, run as a subprocess with stubs. Cite the x-intake contract.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "examples" / "x-intake-local" / "smoke_098_100.py"

# Fail: the probe inherited the smoke process HOME and wrote probe-file there.
# Recover: a fresh temp HOME, and the parent HOME stays empty of probe-file.
HOME_STUB = """#!/bin/sh
printf '%s\\n' "$HOME" > "$PFY_PROBE_OUT"
touch "$HOME/probe-file"
"""

# Fail: TimeoutExpired escaped hook()/hj() (traceback, no receipt) or the 60s/120s
# default ignored PFY_XINTAKE_TIMEOUT so the receipt reason never said timeout.
# Recover: exit 1, a receipt whose reason contains timeout, and no traceback.
SLEEP_STUB = """#!/bin/sh
sleep 30
"""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


class XIntakeSmoke098100Tests(unittest.TestCase):
    def _base_env(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        for key in (
            "SPONSIO_PY",
            "OPEN_STEPS_DIR",
            "HARNESS_BIN",
            "HARNESS_SHA256",
            "PFY_XINTAKE_TIMEOUT",
            "PFY_PROBE_OUT",
        ):
            env.pop(key, None)
        return env

    def _run(self, entry: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "examples/x-intake-local/smoke_098_100.py", "--entry", entry],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=240,
        )

    def _receipt(self, entry: str) -> dict:
        path = ROOT / "pipelines" / "smoke" / entry / "latest.json"
        self.assertTrue(path.is_file(), f"missing receipt {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_fresh_home(self, entry: str, extra_env: dict[str, str]) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-parent-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            probe_out = root / "probe-out"
            stub = root / "stub"
            _write_exe(stub, HOME_STUB)
            env = self._base_env(home)
            env["PFY_PROBE_OUT"] = str(probe_out)
            env.update(extra_env)
            if entry == "repoharness":
                env["HARNESS_BIN"] = str(stub)
                env["HARNESS_SHA256"] = _sha256(stub)
            else:
                env["SPONSIO_PY"] = str(stub)
            proc = self._run(entry, env)
            blob = proc.stdout + proc.stderr
            self.assertTrue(probe_out.is_file(), "stub did not write PFY_PROBE_OUT\n" + blob)
            recorded = os.path.normpath(probe_out.read_text(encoding="utf-8").strip())
            parent = os.path.normpath(str(home))
            # The probe must not inherit the smoke process HOME.
            self.assertNotEqual(
                recorded,
                parent,
                f"probe HOME must be a fresh temp dir, not the parent HOME ({recorded})",
            )
            self.assertFalse((home / "probe-file").exists(), "parent HOME must not contain probe-file")
            temp_root = os.path.normpath(tempfile.gettempdir()) + os.sep
            self.assertTrue(recorded.startswith(temp_root), recorded)
            self.assertNotIn("Traceback", proc.stderr)

    def test_a_sponsio_probe_home_is_fresh_temp(self) -> None:
        self._assert_fresh_home("sponsio", {})

    def test_a_repoharness_home_is_fresh_temp(self) -> None:
        self._assert_fresh_home("repoharness", {})

    def _assert_timeout(self, entry: str, env: dict[str, str]) -> None:
        proc = self._run(entry, env)
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, blob)
        self.assertNotIn("Traceback", proc.stderr)
        reason = self._receipt(entry).get("reason") or ""
        self.assertIn("timeout", reason, blob)

    def test_b_opensteps_timeout_records_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-os-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            hooks = root / "open-steps" / "hooks"
            hooks.mkdir(parents=True)
            _write_exe(hooks / "session-start.sh", SLEEP_STUB)
            _write_exe(hooks / "stop-report.sh", SLEEP_STUB)
            env = self._base_env(home)
            env["OPEN_STEPS_DIR"] = str(root / "open-steps")
            env["PFY_XINTAKE_TIMEOUT"] = "0.2"
            self._assert_timeout("opensteps", env)

    def test_b_repoharness_timeout_records_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-rh-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            stub = root / "harness"
            _write_exe(stub, SLEEP_STUB)
            env = self._base_env(home)
            env["HARNESS_BIN"] = str(stub)
            env["HARNESS_SHA256"] = _sha256(stub)
            env["PFY_XINTAKE_TIMEOUT"] = "0.2"
            self._assert_timeout("repoharness", env)

    def test_c_repoharness_sha256_mismatch_does_not_exec(self) -> None:
        # Fail: any harness binary was executed, so a mismatched pin still ran.
        # Recover: exit 2, reason names the sha256 mismatch, marker stays absent.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-pin-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            marker = root / "executed-marker"
            stub = root / "harness"
            _write_exe(stub, "#!/bin/sh\ntouch %s\n" % marker)
            env = self._base_env(home)
            env["HARNESS_BIN"] = str(stub)
            proc = self._run("repoharness", env)
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 2, blob)
            reason = (self._receipt("repoharness").get("reason") or "").lower()
            self.assertIn("sha256", reason, blob)
            self.assertIn("mismatch", reason, blob)
            self.assertFalse(marker.exists(), "harness stub was executed")
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
