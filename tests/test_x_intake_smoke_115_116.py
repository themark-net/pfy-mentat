"""Entries 115-116 smokes: a child never sees parent env, and a timeout kills the grandchild.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
Fail: a planted key is in the child's environment, or a forked grandchild is alive after the smoke times out.
Recover: the child env has none of the sentinels, and no process running the stub remains.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_RECEIPTS: Path | None = None

# Values are fake. Their names and values must not appear in any tool child's environment.
SENTINELS = {
    "GROK_API_KEY": "sentinel-grok",
    "OPENAI_API_KEY": "sentinel-openai",
    "ANTHROPIC_API_KEY": "sentinel-anthropic",
    "GITHUB_TOKEN": "sentinel-gh",
    "AWS_SECRET_ACCESS_KEY": "sentinel-aws",
    "PFY_LEAK_SENTINEL": "sentinel-parent",
}


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _env_map(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out


def _parent_env(home: Path, **extra: str) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    for key in list(env):
        if key.startswith(("OPENQODEX_", "ASSAY_", "PLAYWRIGHT_")) or key == "PFY_XINTAKE_TIMEOUT":
            env.pop(key, None)
    env.update(SENTINELS)
    env.update(extra)
    if _RECEIPTS is None:
        raise RuntimeError("PFY_SMOKE_RECEIPT_DIR is unset")
    env["PFY_SMOKE_RECEIPT_DIR"] = str(_RECEIPTS)
    return env


def _receipt(entry: str) -> dict:
    path = Path(_RECEIPTS) / entry / "latest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _run(entry: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "examples/x-intake-local/smoke_115_116.py", "--entry", entry],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60,
    )


def _openqodex_tree(root: Path) -> Path:
    pkg = root / "node_modules" / "openqodex"
    (pkg / "dist").mkdir(parents=True)
    (pkg / "package.json").write_text(json.dumps({"version": "0.12.0"}) + "\n", encoding="utf-8")
    (pkg / "dist" / "bin.js").write_text("// stub\n", encoding="utf-8")
    return root


def _assert_child_clean(case: unittest.TestCase, probe: Path, parent_home: Path) -> None:
    text = probe.read_text(encoding="utf-8")
    child = _env_map(text)
    leaked = [key for key, value in SENTINELS.items() if key in child or value in text]
    case.assertEqual(leaked, [])
    case.assertNotEqual(child.get("HOME"), str(parent_home))
    case.assertTrue(child.get("HOME"))


class XIntakeSmoke115116Tests(unittest.TestCase):
    def setUp(self) -> None:
        global _RECEIPTS
        self._receipt_tmp = tempfile.TemporaryDirectory(prefix="pfy-xintake-115-receipts-")
        self.addCleanup(self._receipt_tmp.cleanup)
        _RECEIPTS = Path(self._receipt_tmp.name)

    def tearDown(self) -> None:
        global _RECEIPTS
        _RECEIPTS = None

    def test_version_probes_drop_planted_keys(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-115-") as td:
            home = Path(td, "operator-home")
            home.mkdir()
            node_probe, assay_probe = Path(td, "node-env"), Path(td, "assay-env")
            node_dir = Path(td, "node-bin")
            node_dir.mkdir()
            _write_exe(node_dir / "node", f"""#!/bin/sh
env > {shlex.quote(str(node_probe))}
echo v22.14.0
""")
            # On the tool PATH after --version, so the smoke stops before review.
            _write_exe(node_dir / "claude", "#!/bin/sh\nexit 0\n")
            pkg = _openqodex_tree(Path(td, "openqodex"))
            oq = _run("openqodex", _parent_env(
                home, OPENQODEX_DIR=str(pkg), OPENQODEX_NODE=str(node_dir / "node")))
            self.assertEqual(oq.returncode, 2, oq.stdout + oq.stderr)
            self.assertNotIn("Traceback", oq.stderr)
            _assert_child_clean(self, node_probe, home)

            browsers = Path(td, "browsers")
            browsers.mkdir()
            _write_exe(Path(td, "assay"), f"""#!/bin/sh
env > {shlex.quote(str(assay_probe))}
if [ "$1" = --version ]; then echo "assay 0.3.0"; exit 0; fi
echo ran-page >> {shlex.quote(str(assay_probe))}
exit 1
""")
            ay = _run("assay", _parent_env(
                home, ASSAY_BIN=str(Path(td, "assay")), PLAYWRIGHT_BROWSERS_PATH=str(browsers)))
            self.assertEqual(ay.returncode, 2, ay.stdout + ay.stderr)
            self.assertNotIn("Traceback", ay.stderr)
            self.assertNotIn("ran-page", assay_probe.read_text(encoding="utf-8"))
            _assert_child_clean(self, assay_probe, home)

    def test_timeout_kills_stub_grandchild(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-115-") as td:
            home = Path(td, "operator-home")
            home.mkdir()
            node = Path(td, "node")
            _write_exe(node, """#!/bin/sh
if [ "$1" = --version ]; then echo v22.14.0; exit 0; fi
if [ "$1" = --child ]; then sleep 60; exit 0; fi
"$0" --child >/dev/null 2>&1 &
sleep 60
""")
            pkg = _openqodex_tree(Path(td, "openqodex"))
            env = _parent_env(home, OPENQODEX_DIR=str(pkg), OPENQODEX_NODE=str(node), PFY_XINTAKE_TIMEOUT="1")
            p = _run("openqodex", env)
            time.sleep(0.5)
            left = subprocess.run(["pgrep", "-f", str(node)], capture_output=True, text=True).stdout.split()
            for pid in left:
                try:
                    os.kill(int(pid), 9)
                except OSError:
                    pass
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            receipt = _receipt("openqodex")
            # Fail: the receipt uses its own "timeout after <s>s: <cmd>" sentence.
            # Recover: the reason is the shared timeout_reason text for this entry.
            self.assertEqual(receipt["reason"], "openqodex timeout after 1s", p.stdout + p.stderr)
            self.assertEqual(left, [], "a forked tool grandchild outlived the smoke timeout")

    def test_openqodex_home_outside_temp_area_exits_2(self) -> None:
        outside = Path("/opt/pfy-xintake-not-temp/home")
        self.assertFalse(outside.exists())
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-115-") as td:
            home = Path(td, "operator-home")
            home.mkdir()
            calls = Path(td, "calls")
            node = Path(td, "node")
            _write_exe(node, f"""#!/bin/sh
echo "$@" >> {shlex.quote(str(calls))}
if [ "$1" = --version ]; then echo v22.14.0; exit 0; fi
echo ran-tool >> {shlex.quote(str(calls))}
exit 0
""")
            pkg = _openqodex_tree(Path(td, "openqodex"))
            p = _run("openqodex", _parent_env(
                home, OPENQODEX_DIR=str(pkg), OPENQODEX_NODE=str(node), OPENQODEX_HOME=str(outside)))
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            self.assertIn("temp area", p.stdout)
            text = calls.read_text(encoding="utf-8") if calls.exists() else ""
            self.assertNotIn("ran-tool", text)
            self.assertFalse(outside.exists())

    def test_assay_and_openqodex_receipts_are_ignored(self) -> None:
        for entry in ("assay", "openqodex"):
            rel = f"pipelines/smoke/{entry}/latest.json"
            ignored = subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=str(ROOT))
            self.assertEqual(ignored.returncode, 0, rel)
        tracked = subprocess.run(
            ["git", "check-ignore", "-q", "--", "pipelines/smoke/kolibri1/latest.json"], cwd=str(ROOT))
        self.assertEqual(tracked.returncode, 1)


if __name__ == "__main__":
    unittest.main()
