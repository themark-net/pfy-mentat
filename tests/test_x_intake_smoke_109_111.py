"""Entry 110 (brigade) smoke run as a subprocess with a stub binary: env stripping and timeout cleanup.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
Receipts go to PFY_SMOKE_RECEIPT_DIR, never pipelines/smoke in the repo.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `--version` records whether GROK_API_KEY reached it; any other command forks a sleeping child and sleeps.
# Fail: a paid key reached the tool, or the forked child outlived the timeout (only the direct child was killed).
# Recover: the key is absent in the tool env, and no process running this stub is left after the smoke exits.
STUB = """#!/bin/sh
if [ "$1" = --version ]; then
  if [ -n "${GROK_API_KEY+x}" ]; then echo present > "$PFY_PROBE_OUT"; else echo absent > "$PFY_PROBE_OUT"; fi
  echo "brigade 0.27.0"
  exit 0
fi
if [ "$1" = --child ]; then sleep 60; exit 0; fi
"$0" --child >/dev/null 2>&1 &
sleep 60
"""

# A brigade that satisfies every check and writes only inside its cwd (the scratch repo).
BRIGADE_OK = r"""#!/usr/bin/env python3
import os, subprocess, sys
args = sys.argv[1:]

def emit(obj, code=0):
    sys.stdout.write(__import__("json").dumps(obj) + "\n")
    raise SystemExit(code)

if args[:1] == ["--version"]:
    print("brigade 0.27.0")
    raise SystemExit(0)
if args[:1] == ["init"]:
    os.makedirs(".brigade", exist_ok=True)
    open(".brigade/config.json", "w", encoding="utf-8").write("{}\n")
    raise SystemExit(0)
if args[:3] == ["work", "task", "add"]:
    raise SystemExit(0)
if args[:2] == ["work", "ready"]:
    emit({"ready_count": 1, "ready": [{"id": "t1"}]})
if args[:2] == ["work", "claim"]:
    actor = args[args.index("--actor") + 1]
    if actor == "smoke-a":
        emit({"task_id": "t1", "status": "in_progress", "assignee": "smoke-a"})
    emit({"reason": "no_ready", "exit_code": 1}, 1)
if args[:3] == ["work", "verify", "run"]:
    log = os.path.abspath("stdout.log")
    open(log, "w", encoding="utf-8").write("ok\n")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    failed = "sys.exit(3)" in " ".join(args)
    body = {
        "status": "failed" if failed else "completed",
        "git": {"head": head},
        "commands": [{"exit_code": 3 if failed else 0, "stdout_log_path": log}],
    }
    emit(body, 1 if failed else 0)
if args[:2] == ["receipts", "verify"]:
    counter = os.path.abspath(".verify-count")
    n = int(open(counter, encoding="utf-8").read()) + 1 if os.path.exists(counter) else 1
    open(counter, "w", encoding="utf-8").write(str(n))
    if n == 1:
        emit({"summary": {"ok": 1, "total": 1, "mismatch": 0, "missing": 0}})
    emit({"summary": {"ok": 0, "total": 1, "mismatch": 1, "missing": 0}}, 1)
sys.stderr.write("unhandled brigade args\n")
raise SystemExit(2)
"""

# Records argv, rejects a missing --unshare-pid, and execs the first real binary (the brigade stub).
# PFY_BWRAP_REJECT_UNSHARE=1 makes the probe fail the way an unsupported --unshare-pid does.
BWRAP_FAKE = r"""#!/usr/bin/env python3
import os, sys
log = os.environ.get("PFY_BWRAP_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("\n".join(sys.argv[1:]) + "\n---\n")
if "--unshare-pid" not in sys.argv[1:]:
    raise SystemExit(1)
if os.environ.get("PFY_BWRAP_REJECT_UNSHARE") == "1":
    raise SystemExit(1)
for index, arg in enumerate(sys.argv[1:], 1):
    if os.path.isfile(arg) and os.access(arg, os.X_OK):
        os.execv(arg, sys.argv[index:])
raise SystemExit(0)
"""


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _smoke_tree_sig() -> dict[str, tuple[int, int]]:
    root = ROOT / "pipelines" / "smoke"
    found: dict[str, tuple[int, int]] = {}
    if not root.exists():
        return found
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = Path(dirpath, name)
            st = path.stat()
            found[str(path)] = (st.st_mtime_ns, st.st_size)
    return found


class XIntakeSmoke109111Tests(unittest.TestCase):
    def _run(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "examples/x-intake-local/smoke_109_111.py", "--entry", "brigade"],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120,
        )

    def _assert_repo_smoke_unchanged(self, before: dict[str, tuple[int, int]]) -> None:
        self.assertEqual(_smoke_tree_sig(), before, "pipelines/smoke in the repo changed")
        porcelain = subprocess.run(
            ["git", "status", "--porcelain", "pipelines/smoke"],
            cwd=str(ROOT), capture_output=True, text=True, check=False,
        )
        self.assertEqual(porcelain.stdout, "")

    def test_brigade_strips_grok_key_and_kills_process_group_on_timeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-parent-") as td:
            home, stub, probe = Path(td, "home"), Path(td, "brigade-stub-109"), Path(td, "probe")
            receipts = Path(td, "receipts")
            home.mkdir()
            _write_exe(stub, STUB)
            env = {k: v for k, v in os.environ.items() if not k.startswith("BRIGADE_")}
            env.update(HOME=str(home), BRIGADE_BIN=str(stub), PFY_PROBE_OUT=str(probe),
                       GROK_API_KEY="must-not-leak", PFY_XINTAKE_TIMEOUT="1",
                       PFY_SMOKE_RECEIPT_DIR=str(receipts))
            before = _smoke_tree_sig()
            p = self._run(env)
            time.sleep(0.5)
            left = subprocess.run(["pgrep", "-f", str(stub)], capture_output=True, text=True).stdout.split()
            for pid in left:
                try:
                    os.kill(int(pid), 9)
                except OSError:
                    pass
            self.assertEqual(probe.read_text().strip(), "absent")
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertIn("timeout", receipt["reason"])
            self.assertEqual(left, [], "a forked tool child outlived the smoke timeout")
            self._assert_repo_smoke_unchanged(before)

    def _tool_path(self, bindir: Path, *extra: str) -> None:
        bindir.mkdir()
        git = shutil.which("git")
        py = shutil.which("python3")
        self.assertTrue(git and py, "git and python3 are required on PATH for the brigade smoke")
        os.symlink(git, bindir / "git")
        os.symlink(py, bindir / "python3")
        for name in extra:
            _write_exe(bindir / name, {"bwrap": BWRAP_FAKE}[name])

    def _ok_env(self, home: Path, stub: Path, receipts: Path, path: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("BRIGADE_", "PFY_"))}
        env.update(HOME=str(home), PATH=path, BRIGADE_BIN=str(stub),
                   PFY_SMOKE_RECEIPT_DIR=str(receipts))
        return env

    def test_no_bwrap_records_real_home_snapshot(self) -> None:
        # Fail: bwrap missing and the smoke still claims the bwrap containment, or it skips the real-HOME check.
        # Recover: exit 0, containment real-home-snapshot, real_home_state_unchanged true. A changed snapshot FAILs.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-nobwrap-") as td:
            root = Path(td)
            home, receipts = root / "home", root / "receipts"
            home.mkdir()
            stub = root / "brigade"
            _write_exe(stub, BRIGADE_OK)
            bindir = root / "bin"
            self._tool_path(bindir)
            self.assertIsNone(shutil.which("bwrap", path=str(bindir)))
            env = self._ok_env(home, stub, receipts, str(bindir))
            before = _smoke_tree_sig()
            proc = self._run(env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("containment"), "real-home-snapshot")
            self.assertIs(receipt.get("real_home_state_unchanged"), True)
            self.assertEqual(receipt.get("verdict"), "PASS")
            self._assert_repo_smoke_unchanged(before)

    def test_unshare_pid_is_passed_to_bwrap(self) -> None:
        # Fail: a working bwrap is invoked without --unshare-pid on the tool command.
        # Recover: the wrapped brigade command's argv contains --unshare-pid and the smoke passes.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-unshare-") as td:
            root = Path(td)
            home, receipts = root / "home", root / "receipts"
            home.mkdir()
            stub = root / "brigade"
            _write_exe(stub, BRIGADE_OK)
            bindir = root / "bin"
            self._tool_path(bindir, "bwrap")
            log = root / "bwrap.log"
            env = self._ok_env(home, stub, receipts, str(bindir))
            env["PFY_BWRAP_LOG"] = str(log)
            before = _smoke_tree_sig()
            proc = self._run(env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("containment"), "bwrap-ro-root-no-net")
            text = log.read_text(encoding="utf-8")
            wrapped = [block for block in text.split("---\n") if str(stub) in block]
            self.assertTrue(wrapped, "bwrap never wrapped the brigade binary")
            self.assertIn("--unshare-pid", wrapped[0])
            self._assert_repo_smoke_unchanged(before)

    def test_unshare_pid_unsupported_falls_back(self) -> None:
        # Fail: an unsupported --unshare-pid is retried without the flag, or the tool never runs.
        # Recover: the probe argv contains --unshare-pid, the prefix is dropped, containment is the
        # real-HOME snapshot, and the brigade stub still runs to a pass.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-unshare-no-") as td:
            root = Path(td)
            home, receipts = root / "home", root / "receipts"
            home.mkdir()
            stub = root / "brigade"
            _write_exe(stub, BRIGADE_OK)
            bindir = root / "bin"
            self._tool_path(bindir, "bwrap")
            log = root / "bwrap.log"
            env = self._ok_env(home, stub, receipts, str(bindir))
            env["PFY_BWRAP_LOG"] = str(log)
            env["PFY_BWRAP_REJECT_UNSHARE"] = "1"
            before = _smoke_tree_sig()
            proc = self._run(env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("containment"), "real-home-snapshot")
            self.assertIs(receipt.get("real_home_state_unchanged"), True)
            text = log.read_text(encoding="utf-8")
            self.assertIn("--unshare-pid", text)
            self.assertNotIn(str(stub), text, "tool command was still wrapped after the probe failed")
            self._assert_repo_smoke_unchanged(before)


if __name__ == "__main__":
    unittest.main()
