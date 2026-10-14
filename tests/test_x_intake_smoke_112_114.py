"""Entries 112-114 smoke: child env is the reduced allowlist, and a timeout kills grandchildren.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOW = {"HOME", "PATH", "TERM", "LANG", "NO_COLOR"}
# Fake values only. A child that still sees the parent env fails the test.
SENTINELS = {
    "GROK_API_KEY": "pfy-sentinel-grok",
    "OPENAI_API_KEY": "pfy-sentinel-openai",
    "ANTHROPIC_API_KEY": "pfy-sentinel-anthropic",
    "AWS_SECRET_ACCESS_KEY": "pfy-sentinel-aws",
    "GITHUB_TOKEN": "pfy-sentinel-github",
    "PFY_SENTINEL_PARENT": "pfy-sentinel-parent",
}

# --version dumps the execve environment and prints a new-enough Node. Any other command exits 0
# without creating an agent, so the smoke stops at the folder check.
NODE_VERSION_STUB = """#!/usr/bin/python3
import os
import sys
from pathlib import Path
out = Path(__file__).resolve().parent / "node.environ"
if sys.argv[1:2] == ["--version"]:
    lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
    out.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    print("v22.19.0")
raise SystemExit(0)
"""

# Prints a commit that will not match the pin, after dumping the execve environment.
GIT_STUB = """#!/usr/bin/python3
import os
from pathlib import Path
out = Path(__file__).resolve().parent / "git.environ"
lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
out.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
print("not-a-real-commit")
"""

# Not --version: dirty the baked-in real ~/overtime, fork a sleeper, then sleep.
# Fail: the sleeper is still alive after the smoke, or the receipt never reports the dirty home.
# Recover: the process group is gone, and the receipt names the real-HOME check.
GRANDCHILD_STUB = """#!/bin/sh
if [ "$1" = "--version" ]; then
  echo v22.19.0
  exit 0
fi
if [ "$1" = "--grandchild" ]; then
  sleep 60
  exit 0
fi
mkdir -p "__PARENT_OT__"
echo touched > "__PARENT_OT__/marker"
"$0" --grandchild __MARKER__ >/dev/null 2>&1 &
sleep 60
"""


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _overtime_tree(root: Path) -> Path:
    pkg = root / "node_modules" / "@ukanwat" / "overtime"
    (pkg / "dist").mkdir(parents=True)
    (pkg / "dist" / "bin.js").write_text("// stub\n", encoding="utf-8")
    (pkg / "package.json").write_text('{"version": "0.5.3"}\n', encoding="utf-8")
    return root


def _parent_env(home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    for key in (
        "OVERTIME_DIR", "OVERTIME_NODE", "OVERTIME_VERSION",
        "FEST_BIN", "FEST_SHA256", "CAMP_SHA256",
        "SLOPTRIM_DIR", "SLOPTRIM_COMMIT",
        "PFY_XINTAKE_TIMEOUT",
    ):
        env.pop(key, None)
    env.update(SENTINELS)
    return env


def _run(entry: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "examples/x-intake-local/smoke_112_114.py", "--entry", entry],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60,
    )


def _receipt(entry: str) -> dict:
    path = ROOT / "pipelines" / "smoke" / entry / "latest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _seen(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out


class XIntakeSmoke112114Tests(unittest.TestCase):
    def test_node_version_and_git_rev_parse_do_not_see_parent_sentinels(self) -> None:
        # Fail: node --version or sloptrim's git rev-parse inherits the parent env, so a planted
        # key is visible or HOME is still the parent HOME.
        # Recover: the child env is only PATH/HOME/TERM/LANG/NO_COLOR and HOME is a different temp dir.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-112-env-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            with self.subTest("overtime node --version"):
                ot = _overtime_tree(root / "overtime")
                node = root / "node-stub"
                _write_exe(node, NODE_VERSION_STUB)
                env = _parent_env(home)
                env["OVERTIME_DIR"] = str(ot)
                env["OVERTIME_NODE"] = str(node)
                proc = _run("overtime", env)
                blob = proc.stdout + proc.stderr
                self.assertNotIn("Traceback", proc.stderr, blob)
                probe = root / "node.environ"
                self.assertTrue(probe.is_file(), blob)
                seen = _seen(probe.read_text(encoding="utf-8"))
                self.assertLessEqual(set(seen), ALLOW, sorted(set(seen) - ALLOW))
                for key, value in SENTINELS.items():
                    self.assertNotIn(key, seen)
                    self.assertNotIn(value, probe.read_text(encoding="utf-8"))
                self.assertNotEqual(Path(seen["HOME"]).resolve(), home.resolve())
            with self.subTest("sloptrim git rev-parse"):
                slop = root / "sloptrim" / "scripts"
                slop.mkdir(parents=True)
                (slop / "detect.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
                bindir = root / "bin"
                bindir.mkdir()
                _write_exe(bindir / "git", GIT_STUB)
                env = _parent_env(home)
                env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
                env["SLOPTRIM_DIR"] = str(root / "sloptrim")
                proc = _run("sloptrim", env)
                blob = proc.stdout + proc.stderr
                self.assertNotIn("Traceback", proc.stderr, blob)
                self.assertEqual(proc.returncode, 2, blob)
                probe = bindir / "git.environ"
                self.assertTrue(probe.is_file(), blob)
                seen = _seen(probe.read_text(encoding="utf-8"))
                self.assertLessEqual(set(seen), ALLOW, sorted(set(seen) - ALLOW))
                for key, value in SENTINELS.items():
                    self.assertNotIn(key, seen)
                    self.assertNotIn(value, probe.read_text(encoding="utf-8"))
                self.assertNotEqual(Path(seen["HOME"]).resolve(), home.resolve())

    def test_timeout_kills_grandchild_and_still_checks_real_home(self) -> None:
        # Fail: PFY_XINTAKE_TIMEOUT kills only the direct child, so the stub's grandchild is still
        # alive, or the timeout returns before the ~/overtime compare.
        # Recover: the grandchild is dead and the receipt reports that the real HOME changed.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-112-gc-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            parent_ot = home / "overtime"
            marker = f"pfy-grandchild-112-{os.getpid()}"
            ot = _overtime_tree(root / "overtime-pkg")
            node = root / "node-stub"
            body = GRANDCHILD_STUB.replace("__PARENT_OT__", str(parent_ot)).replace("__MARKER__", marker)
            _write_exe(node, body)
            env = _parent_env(home)
            env["OVERTIME_DIR"] = str(ot)
            env["OVERTIME_NODE"] = str(node)
            env["PFY_XINTAKE_TIMEOUT"] = "1"
            left: list[str] = []
            try:
                proc = _run("overtime", env)
            finally:
                time.sleep(0.5)
                left = subprocess.run(
                    ["pgrep", "-f", marker], capture_output=True, text=True,
                ).stdout.split()
                for pid in left:
                    try:
                        os.kill(int(pid), 9)
                    except OSError:
                        pass
            blob = proc.stdout + proc.stderr
            self.assertNotIn("Traceback", proc.stderr, blob)
            self.assertEqual(proc.returncode, 1, blob)
            self.assertTrue((parent_ot / "marker").is_file(), blob)
            receipt = _receipt("overtime")
            self.assertIn("real HOME ~/overtime was created or changed", receipt.get("reason") or "", blob)
            self.assertEqual(left, [], "a forked tool grandchild outlived the smoke timeout")


if __name__ == "__main__":
    unittest.main()
