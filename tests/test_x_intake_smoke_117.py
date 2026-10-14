"""Entry 117 smoke: a child never sees parent env, a timeout kills the grandchild, unstaged exits 2.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
Fail: a planted key is in the child's environment, a forked grandchild is alive after the timeout,
or a missing venv exits anything but 2.
Recover: the child env has none of the sentinels, no process running the stub remains, and the
unstaged run exits 2 before it starts a tool.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Values are fake. Their names and values must not appear in any tool child's environment.
SENTINELS = {
    "GROK_API_KEY": "sentinel-grok",
    "OPENAI_API_KEY": "sentinel-openai",
    "ANTHROPIC_API_KEY": "sentinel-anthropic",
    "NVIDIA_API_KEY": "sentinel-nvidia",
    "TAVILY_API_KEY": "sentinel-tavily",
    "NGC_API_KEY": "sentinel-ngc",
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
        if key.startswith("AIQ_") or key == "PFY_XINTAKE_TIMEOUT":
            env.pop(key, None)
    env.update(SENTINELS)
    env.update(extra)
    return env


def _run(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "examples/x-intake-local/smoke_117.py", "--entry", "aiq"],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60,
    )


class _TagsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b'{"models":[{"name":"qwen3.6:35b"}]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def _serve_tags() -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _TagsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, f"http://{host}:{port}"


def _assert_child_clean(case: unittest.TestCase, probe: Path, parent_home: Path) -> None:
    text = probe.read_text(encoding="utf-8")
    child = _env_map(text)
    leaked = [key for key, value in SENTINELS.items() if key in child or value in text]
    case.assertEqual(leaked, [])
    api_keys = [key for key in child if key.endswith("_API_KEY") or "TAVILY" in key or "NGC" in key]
    case.assertEqual(api_keys, [])
    case.assertNotEqual(child.get("HOME"), str(parent_home))
    case.assertTrue(child.get("HOME"))


class XIntakeSmoke117Tests(unittest.TestCase):
    def test_sentinel_keys_never_reach_the_child(self) -> None:
        server, base = _serve_tags()
        try:
            with tempfile.TemporaryDirectory(prefix="pfy-xintake-117-") as td:
                home = Path(td, "operator-home")
                home.mkdir()
                probe = Path(td, "child-env")
                nat = Path(td, "nat")
                _write_exe(nat, f"""#!/bin/sh
env >> {shlex.quote(str(probe))}
if [ "$1" = --version ]; then echo "nat 1.8.0"; exit 0; fi
printf '%s\\n' '--------------------------------------------------' 'Workflow Result:' 'A short local research report about Rust news with a citation.' '--------------------------------------------------'
exit 0
""")
                ran = _run(_parent_env(home, AIQ_BIN=str(nat), AIQ_OLLAMA_URL=base, AIQ_ROOT=str(Path(td, "empty"))))
                self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr)
                self.assertNotIn("Traceback", ran.stderr)
                _assert_child_clean(self, probe, home)
        finally:
            server.shutdown()
            server.server_close()

    def test_timeout_kills_stub_grandchild(self) -> None:
        server, base = _serve_tags()
        try:
            with tempfile.TemporaryDirectory(prefix="pfy-xintake-117-") as td:
                home = Path(td, "operator-home")
                home.mkdir()
                nat = Path(td, "nat")
                _write_exe(nat, """#!/bin/sh
if [ "$1" = --version ]; then echo "nat 1.8.0"; exit 0; fi
if [ "$1" = --child ]; then sleep 60; exit 0; fi
"$0" --child >/dev/null 2>&1 &
sleep 60
""")
                ran = _run(_parent_env(
                    home, AIQ_BIN=str(nat), AIQ_OLLAMA_URL=base, AIQ_ROOT=str(Path(td, "empty")),
                    PFY_XINTAKE_TIMEOUT="1",
                ))
                time.sleep(0.5)
                left = subprocess.run(["pgrep", "-f", str(nat)], capture_output=True, text=True).stdout.split()
                for pid in left:
                    try:
                        os.kill(int(pid), 9)
                    except OSError:
                        pass
                self.assertEqual(ran.returncode, 1, ran.stdout + ran.stderr)
                self.assertNotIn("Traceback", ran.stderr)
                receipt = json.loads((ROOT / "pipelines/smoke/aiq/latest.json").read_text(encoding="utf-8"))
                self.assertIn("timeout", receipt["reason"])
                self.assertEqual(left, [], "a forked tool grandchild outlived the smoke timeout")
        finally:
            server.shutdown()
            server.server_close()

    def test_unstaged_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-117-") as td:
            home = Path(td, "operator-home")
            home.mkdir()
            empty = Path(td, "empty-stage")
            empty.mkdir()
            ran = _run(_parent_env(home, AIQ_ROOT=str(empty)))
            self.assertEqual(ran.returncode, 2, ran.stdout + ran.stderr)
            self.assertNotIn("Traceback", ran.stderr)
            self.assertIn("not staged", ran.stdout)
            receipt = json.loads((ROOT / "pipelines/smoke/aiq/latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["verdict"], "FAIL_CANNOT_RUN_HERE")

    def test_aiq_receipt_is_ignored(self) -> None:
        rel = "pipelines/smoke/aiq/latest.json"
        ignored = subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=str(ROOT))
        self.assertEqual(ignored.returncode, 0, rel)
        tracked = subprocess.run(
            ["git", "check-ignore", "-q", "--", "pipelines/smoke/kolibri1/latest.json"], cwd=str(ROOT))
        self.assertEqual(tracked.returncode, 1)


if __name__ == "__main__":
    unittest.main()
