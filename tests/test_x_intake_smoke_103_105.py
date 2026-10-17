"""Entries 103-105 smokes: sha pin/env for graphjin, and graphjin_world log cleanup.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
"""
from __future__ import annotations

import builtins
import gc
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "x-intake-local"))
from smoke import PAID_KEYS  # noqa: E402
from smoke_103_105 import GRAPHJIN_V3216_SHA256  # noqa: E402

DUMMY_PAID = "pfy-test-dummy"
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

    def test_node_version_uses_clean_env(self) -> None:
        # Fail: `node --version` inherits PAID_KEYS or the parent HOME.
        # Recover: the version probe runs, its HOME is a fresh temp dir, and no paid name or dummy value is present.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-nodever-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            probe = root / "node.env"
            node = root / "node"
            _write_exe(node, "#!/bin/sh\nif [ \"$1\" = --version ]; then env > %s; echo v22.0.0; exit 0; fi\nexit 0\n" % shlex.quote(str(probe)))
            binary = root / "bugpatrol"
            _write_exe(binary, "#!/bin/sh\nexit 0\n")
            env = self._base_env(home)
            for key in PAID_KEYS:
                env[key] = DUMMY_PAID
            for key in ("GH_TOKEN", "GITHUB_TOKEN", "NPM_TOKEN", "FOO_API_KEY"):
                env[key] = DUMMY_PAID
            env["PFY_SMOKE_RECEIPT_DIR"] = str(root / "receipts")
            env["BUGPATROL_BIN"] = str(binary)
            env["BUGPATROL_NODE"] = str(node)
            proc = subprocess.run(
                ["python3", "examples/x-intake-local/smoke_103_105.py", "--entry", "bugpatrol"],
                cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60,
            )
            self.assertTrue(probe.is_file(), proc.stdout + proc.stderr)
            dump = probe.read_text(encoding="utf-8")
            leaked = sorted(
                {line.split("=", 1)[0] for line in dump.splitlines() if line.split("=", 1)[0] in PAID_KEYS}
            )
            self.assertEqual(leaked, [], f"node --version received paid keys {leaked}")
            self.assertFalse(DUMMY_PAID in dump, "node --version received the dummy paid value")
            names = {line.split("=", 1)[0] for line in dump.splitlines()}
            secret_names = [key for key in ("GH_TOKEN", "GITHUB_TOKEN", "NPM_TOKEN", "FOO_API_KEY") if key in names]
            self.assertEqual(secret_names, [], f"node --version received secret names {secret_names}")
            self.assertIn("PATH", names)
            self.assertTrue(any(line.startswith("PATH=") and line.split("=", 1)[1] for line in dump.splitlines()))
            homes = [line.split("=", 1)[1] for line in dump.splitlines() if line.startswith("HOME=")]
            self.assertEqual(len(homes), 1, "node --version env dump has no HOME")
            self.assertNotEqual(os.path.normpath(homes[0]), os.path.normpath(str(home)))
            self.assertTrue(homes[0].startswith(os.path.normpath(tempfile.gettempdir()) + os.sep), homes[0])
            self.assertNotIn("Traceback", proc.stderr)

    def test_graphjin_child_drops_secret_shaped_env(self) -> None:
        # Fail: the graphjin child keeps secret-shaped names (M26) or GITHUB_PAT (M28).
        # Recover: those names are absent, PATH is present, and HOME is a fresh temp dir.
        secret_names = (
            "NPM_TOKEN", "GITHUB_PAT", "GH_ENTERPRISE_TOKEN", "HF_TOKEN",
            "FOO_API_KEY", "DB_PASSWORD", "MY_SECRET", "AWS_CREDENTIALS",
        )
        stub_body = """#!/usr/bin/env python3
import os
from pathlib import Path
here = Path(__file__).resolve().parent
(here / "graphjin-env-names").write_text("\\n".join(sorted(os.environ)) + "\\n")
(here / "graphjin-home-value").write_text(os.environ.get("HOME", ""))
raise SystemExit(1)
"""
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-gj-env-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            stub = root / "graphjin"
            _write_exe(stub, stub_body)
            env = self._base_env(home)
            env["GRAPHJIN_BIN"] = str(stub)
            env["GRAPHJIN_SHA256"] = hashlib.sha256(stub.read_bytes()).hexdigest()
            env["PFY_SMOKE_RECEIPT_DIR"] = str(root / "receipts")
            for key in secret_names:
                env[key] = DUMMY_PAID
            proc = self._run(env)
            blob = proc.stdout + proc.stderr
            names_path = root / "graphjin-env-names"
            self.assertTrue(names_path.is_file(), blob)
            seen = names_path.read_text(encoding="utf-8").splitlines()
            self.assertFalse(any("=" in line for line in seen), "env dump included values")
            leaked = [key for key in secret_names if key in seen]
            self.assertEqual(leaked, [], f"graphjin child saw secret names {leaked}")
            self.assertIn("PATH", seen)
            home_value = (root / "graphjin-home-value").read_text(encoding="utf-8").strip()
            self.assertNotEqual(os.path.normpath(home_value), os.path.normpath(str(home)))
            self.assertTrue(home_value.startswith(os.path.normpath(tempfile.gettempdir()) + os.sep), home_value)
            self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
