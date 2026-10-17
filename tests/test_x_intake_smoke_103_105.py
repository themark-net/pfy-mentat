"""Entries 103-105 smokes: sha pin/env for graphjin, and graphjin_world log cleanup.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
"""
from __future__ import annotations

import builtins
import gc
import json
import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "x-intake-local"))
from smoke_103_105 import GRAPHJIN_V3216_SHA256  # noqa: E402
import smoke_103_105  # noqa: E402

OTHER_SHA = "0123456789abcdef" * 4


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


class XIntakeSmoke103105Tests(unittest.TestCase):
    def _base_env(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        for key in ("GRAPHJIN_BIN", "GRAPHJIN_SHA256", "PFY_XINTAKE_TIMEOUT"):
            env.pop(key, None)
        return env

    def _run(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "examples/x-intake-local/smoke_103_105.py", "--entry", "graphjin"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def _receipt(self) -> dict:
        path = ROOT / "pipelines" / "smoke" / "graphjin" / "latest.json"
        self.assertTrue(path.is_file(), f"missing receipt {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _graphjin_sha(self, override: str | None) -> None:
        # Fail: a mismatched pin still execs, or the receipt omits expected source/value,
        # or an override is silent. Recover: exit 2, no exec, source pin or env, WARN only for env.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-gj-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            marker = root / "executed-marker"
            stub = root / "graphjin"
            _write_exe(stub, "#!/bin/sh\ntouch %s\n" % marker)
            env = self._base_env(home)
            env["GRAPHJIN_BIN"] = str(stub)
            if override is not None:
                env["GRAPHJIN_SHA256"] = override
            proc = self._run(env)
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 2, blob)
            self.assertFalse(marker.exists(), "graphjin stub was executed")
            self.assertNotIn("Traceback", proc.stderr)
            got = (self._receipt().get("expected") or {}).get("GRAPHJIN_SHA256") or {}
            self.assertEqual(got.get("pin"), GRAPHJIN_V3216_SHA256, blob)
            if override is None:
                self.assertNotIn("WARN:", proc.stderr)
                self.assertEqual(got.get("source"), "pin", blob)
                self.assertEqual(got.get("value"), GRAPHJIN_V3216_SHA256, blob)
            else:
                warn = f"WARN: $GRAPHJIN_SHA256={override} overrides the pinned {GRAPHJIN_V3216_SHA256}"
                self.assertIn(warn, proc.stderr)
                self.assertEqual(got.get("source"), "env", blob)
                self.assertEqual(got.get("value"), override, blob)

    def test_graphjin_sha_unset_records_pin_and_does_not_exec(self) -> None:
        self._graphjin_sha(None)

    def test_graphjin_sha_env_warns_records_override_and_does_not_exec(self) -> None:
        self._graphjin_sha(OTHER_SHA)

    def test_graphjin_sha_env_equal_to_pin_does_not_warn(self) -> None:
        # Fail: an env value equal to the pin (any hex case) still prints WARN.
        # Recover: exit 2, no exec, source env, value is the pin, stderr has no WARN.
        for override in (GRAPHJIN_V3216_SHA256, GRAPHJIN_V3216_SHA256.upper()):
            with self.subTest(override=override[:12]):
                with tempfile.TemporaryDirectory(prefix="pfy-xintake-gj-eq-") as td:
                    root = Path(td)
                    home = root / "home"
                    home.mkdir()
                    marker = root / "executed-marker"
                    stub = root / "graphjin"
                    _write_exe(stub, "#!/bin/sh\ntouch %s\n" % marker)
                    env = self._base_env(home)
                    env["GRAPHJIN_BIN"] = str(stub)
                    env["GRAPHJIN_SHA256"] = override
                    proc = self._run(env)
                    blob = proc.stdout + proc.stderr
                    self.assertEqual(proc.returncode, 2, blob)
                    self.assertFalse(marker.exists(), "graphjin stub was executed")
                    self.assertNotIn("WARN:", proc.stderr, blob)
                    got = (self._receipt().get("expected") or {}).get("GRAPHJIN_SHA256") or {}
                    self.assertEqual(got.get("source"), "env", blob)
                    self.assertEqual(got.get("value"), GRAPHJIN_V3216_SHA256, blob)
                    self.assertEqual(got.get("pin"), GRAPHJIN_V3216_SHA256, blob)

    def test_graphjin_world_closes_log_when_popen_raises(self) -> None:
        # Fail: Popen raises after serve.log is opened and the handle stays open.
        # Recover: the OSError still propagates and the serve.log handle is closed.
        held: list = []
        real_open = builtins.open

        def tracking_open(*args, **kwargs):
            fh = real_open(*args, **kwargs)
            target = args[0] if args else kwargs.get("file", "")
            if str(target).endswith("serve.log"):
                held.append(fh)
            return fh

        with warnings.catch_warnings():
            warnings.simplefilter("error", ResourceWarning)
            with patch("subprocess.Popen", side_effect=OSError("popen failed")), patch("builtins.open", tracking_open):
                with self.assertRaises(OSError):
                    smoke_103_105.graphjin_world("dummy-graphjin", False, False, {}, "read_only")
            gc.collect()
        self.assertTrue(held, "serve.log was not opened")
        self.assertTrue(held[-1].closed)

    def test_graphjin_world_early_exit_records_log_tail_and_closes(self) -> None:
        # Fail: the server exits before /health and the serve.log handle leaks, or the receipt
        # has no log tail. Recover: the tail contains what the server wrote, and the handle is closed.
        held: list = []
        real_open = builtins.open

        def tracking_open(*args, **kwargs):
            fh = real_open(*args, **kwargs)
            target = args[0] if args else kwargs.get("file", "")
            if str(target).endswith("serve.log"):
                held.append(fh)
            return fh

        with tempfile.TemporaryDirectory(prefix="pfy-xintake-gj-exit-") as td:
            stub = Path(td) / "graphjin"
            stub.write_text("#!/bin/sh\necho pfy-serve-log-tail\nexit 1\n", encoding="utf-8")
            stub.chmod(0o755)
            receipt: dict = {}
            with warnings.catch_warnings():
                warnings.simplefilter("error", ResourceWarning)
                with patch("builtins.open", tracking_open):
                    got = smoke_103_105.graphjin_world(str(stub), True, False, receipt, "read_only")
                gc.collect()
            self.assertIsNone(got)
            self.assertIn("pfy-serve-log-tail", receipt.get("read_only_log") or "")
            self.assertEqual(receipt.get("reason"), "graphjin did not come up (read_only)")
            self.assertTrue(held, "serve.log was not opened")
            self.assertTrue(held[-1].closed)


if __name__ == "__main__":
    unittest.main()
