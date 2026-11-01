"""pfy tells a harness whether it sees the host tree or the cage bind (T-0108)."""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"


def _chunk() -> str:
    text = PFY.read_text(encoding="utf-8")
    start = text.index("print_fs_nav()")
    end = text.index("\nstub_harness()")
    return text[start:end]


def _extract(text: str, name: str) -> str:
    marker = name + "() {"
    start = text.index(marker)
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise RuntimeError("unbalanced " + name)


def _run_continue_stub(state: Path) -> subprocess.CompletedProcess[str]:
    """Run stub_harness continue. PATH has python3 and mkdir only, so no IDE binary is present."""
    text = PFY.read_text(encoding="utf-8")
    body = "\n".join(
        [
            _extract(text, "have"),
            _extract(text, "json_field"),
            _extract(text, "print_fs_nav"),
            _extract(text, "write_continue_config"),
            _extract(text, "stub_harness"),
            "stub_harness continue",
        ]
    )
    python = shutil.which("python3")
    mkdir = shutil.which("mkdir")
    if not python or not mkdir:
        raise RuntimeError("python3 and mkdir must be on PATH")
    bindir = state / "bin"
    bindir.mkdir()
    os.symlink(python, bindir / "python3")
    os.symlink(mkdir, bindir / "mkdir")
    script = "\n".join(
        [
            "set -euo pipefail",
            "ROOT=" + shlex.quote(str(ROOT)),
            'REG="$ROOT/data/harnesses.json"',
            "STATE_DIR=" + shlex.quote(str(state)),
            "HOME=" + shlex.quote(str(state)),
            body,
        ]
    )
    return subprocess.run(
        ["/bin/bash", "-c", script],
        cwd=state,
        capture_output=True,
        text=True,
        env={"PATH": str(bindir), "HOME": str(state), "PFY_STATE_DIR": str(state)},
        timeout=30,
    )


class FsNavTests(unittest.TestCase):
    def test_host_root_is_direct_and_names_the_cage_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            env.pop("PFY_FS", None)
            env.pop("AGENTCAGE_DIR", None)
            script = _chunk() + '\nROOT="/home/mark/DEVELOP/pfy-mentat"\nprint_fs_nav\nprintf "%s\\n" "$PFY_FS"\n'
            proc = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("filesystem: direct", proc.stdout)
        self.assertIn("root: /home/mark/DEVELOP/pfy-mentat", proc.stdout)
        self.assertIn(f"{tmp}/.agentcage/workspace/pfy-mentat", proc.stdout)
        self.assertIn("make cage-code-sync", proc.stdout)
        self.assertTrue(proc.stdout.strip().endswith("direct"))

    def test_workspace_root_is_cage(self):
        env = os.environ.copy()
        env.pop("PFY_FS", None)
        script = _chunk() + '\nROOT="/workspace/pfy-mentat"\nprint_fs_nav\nprintf "%s\\n" "$PFY_FS_ROOT"\n'
        proc = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("filesystem: cage", proc.stdout)
        self.assertIn("filesystem MCP", proc.stdout)
        self.assertTrue(proc.stdout.strip().endswith("/workspace/pfy-mentat"))

    def test_continue_config_uses_live_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["STATE_DIR"] = tmp
            env["LOCAL_OPENAI_BASE_URL"] = "http://127.0.0.1:11434"
            script = _chunk() + "\nwrite_continue_config\n"
            proc = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
            doc = json.loads((Path(tmp) / "continue-config.json").read_text(encoding="utf-8"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(doc["models"][0]["apiBase"], "http://127.0.0.1:11434/v1")
        self.assertIn("apiBase: http://127.0.0.1:11434/v1", proc.stdout)

    def test_continue_stub_prints_filesystem_and_does_not_exec(self):
        """Fail: the continue stub exits 0, skips the config, or execs a binary.
        Recover: exit 2, print filesystem and STUB harness: continue, write continue-config.json.
        """
        scratch = ROOT / "tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="fs-nav-continue-", dir=scratch) as tmp:
            state = Path(tmp)
            proc = _run_continue_stub(state)
            cfg = state / "continue-config.json"
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("filesystem:", proc.stdout)
            self.assertIn("STUB harness: continue", proc.stdout)
            self.assertTrue(cfg.is_file(), proc.stdout + proc.stderr)
            doc = json.loads(cfg.read_text(encoding="utf-8"))
        self.assertEqual(doc["models"][0]["apiBase"], "http://127.0.0.1:1919/v1")


if __name__ == "__main__":
    unittest.main()
