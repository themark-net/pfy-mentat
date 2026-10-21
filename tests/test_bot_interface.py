"""Bot interface fail and recover. Fake processes and a local HTTP probe. No Ollama."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "pfylib" / "bot_interface.py"
DRIVER = ROOT / "pfylib" / "hermes_bot_driver.py"


def _fake(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _opencode_script(stamp: Path) -> str:
    return (
        "#!/bin/sh\n"
        f"printf '%s\\n' opencode-ok > {json.dumps(str(stamp))}\n"
        "echo opencode-ok\n"
        "exit 0\n"
    )


def _sleep_script(pid_file: Path) -> str:
    return (
        "#!/usr/bin/env python3\n"
        "import os, time\n"
        f"open({json.dumps(str(pid_file))}, 'w', encoding='utf-8').write(str(os.getpid()))\n"
        "time.sleep(30)\n"
    )


def _bad_script() -> str:
    return (
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "out = Path(args[args.index('--out') + 1])\n"
        "out.write_text(json.dumps({\n"
        "    'ok': True,\n"
        "    'final_text': 'x',\n"
        "    'tool_calls': [{'name': 'submit', 'arguments': 'nope'}],\n"
        "}), encoding='utf-8')\n"
    )


class _Tags(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = b'{"models":[]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


class BotInterfaceTests(unittest.TestCase):
    def _server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Tags)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return f"http://127.0.0.1:{server.server_address[1]}/v1"

    def _run(self, prompt, env, timeout=15):
        proc = subprocess.run(
            [sys.executable, str(BOT), prompt],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ROOT,
        )
        return proc

    def _env(self, **extra):
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin"),
            "HOME": os.environ.get("HOME", str(Path.home())),
            "LANG": "C.UTF-8",
            "PFY_ROOT": str(ROOT),
            "PFY_BOT_TIMEOUT": "5",
        }
        env.update(extra)
        return env

    def test_default_is_opencode_and_does_not_start_hermes(self):
        import tempfile

        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hermes = tmp_path / "hermes.py"
            stamp = tmp_path / "hermes-started"
            _fake(hermes, _sleep_script(stamp))
            opencode = tmp_path / "opencode"
            seen = tmp_path / "opencode-stamp"
            _fake(opencode, _opencode_script(seen))
            proc = self._run(
                "hello",
                self._env(
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_HERMES_PYTHON=str(hermes),
                    PFY_BOT_OPENCODE=str(opencode),
                ),
            )
            self.assertFalse(stamp.exists())
            self.assertTrue(seen.exists())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("bot interface: opencode", proc.stdout)
        self.assertIn("reasoning: off", proc.stdout)
        self.assertIn("opencode-ok", proc.stdout)
        self.assertNotIn("install.sh", proc.stdout + proc.stderr)

    def test_hermes_missing_falls_back_to_opencode(self):
        import tempfile

        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            opencode = tmp_path / "opencode"
            seen = tmp_path / "opencode-stamp"
            _fake(opencode, _opencode_script(seen))
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_HERMES_PYTHON=str(tmp_path / "missing-python"),
                    PFY_HERMES_CHECKOUT=str(tmp_path / "missing-checkout"),
                    PFY_HERMES_HOME=str(tmp_path / "home"),
                    PFY_BOT_OPENCODE=str(opencode),
                ),
            )
            self.assertTrue(seen.exists())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("falling back to opencode", proc.stdout)
        self.assertIn("opencode-ok", proc.stdout)
        self.assertNotIn("install.sh", proc.stdout + proc.stderr)

    def test_hermes_and_opencode_missing_names_the_attach_recovery(self):
        import tempfile

        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_HERMES_PYTHON=str(tmp_path / "missing-python"),
                    PFY_HERMES_CHECKOUT=str(tmp_path / "missing-checkout"),
                    PFY_HERMES_HOME=str(tmp_path / "home"),
                    PFY_BOT_OPENCODE=str(tmp_path / "missing-opencode"),
                ),
            )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("falling back to opencode", proc.stdout)
        self.assertIn("bot interface: opencode", proc.stdout)
        self.assertIn("./pfy attach opencode", proc.stdout)
        self.assertNotIn("install.sh", proc.stdout + proc.stderr)

    def test_fallback_does_not_start_opencode_when_the_model_server_is_down(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            opencode = tmp_path / "opencode"
            seen = tmp_path / "opencode-stamp"
            _fake(opencode, _opencode_script(seen))
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL="http://127.0.0.1:9/v1",
                    PFY_HERMES_PYTHON=str(tmp_path / "missing-python"),
                    PFY_HERMES_CHECKOUT=str(tmp_path / "missing-checkout"),
                    PFY_HERMES_HOME=str(tmp_path / "home"),
                    PFY_BOT_OPENCODE=str(opencode),
                ),
            )
            self.assertFalse(seen.exists())
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("model server down", proc.stdout)
        self.assertIn("./pfy up", proc.stdout)
        self.assertNotIn("install.sh", proc.stdout + proc.stderr)

    def test_model_server_down_does_not_start_the_driver(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hermes = tmp_path / "hermes.py"
            pid = tmp_path / "pid"
            _fake(hermes, _sleep_script(pid))
            checkout = tmp_path / "checkout"
            checkout.mkdir()
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL="http://127.0.0.1:9/v1",
                    PFY_HERMES_PYTHON=str(hermes),
                    PFY_HERMES_CHECKOUT=str(checkout),
                    PFY_HERMES_HOME=str(tmp_path / "home"),
                    PFY_BOT_DRIVER=str(DRIVER),
                ),
            )
            self.assertFalse(pid.exists())
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("model server down", proc.stdout)
        self.assertIn("./pfy up", proc.stdout)

    def test_malformed_tool_call_is_a_failure(self):
        import tempfile

        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hermes = tmp_path / "hermes.py"
            _fake(hermes, _bad_script())
            checkout = tmp_path / "checkout"
            checkout.mkdir()
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_HERMES_PYTHON=str(hermes),
                    PFY_HERMES_CHECKOUT=str(checkout),
                    PFY_HERMES_HOME=str(tmp_path / "home"),
                ),
            )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("malformed tool call", proc.stdout)

    def test_timeout_kills_the_child(self):
        import tempfile

        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            hermes = tmp_path / "hermes.py"
            pid_file = tmp_path / "pid"
            _fake(hermes, _sleep_script(pid_file))
            checkout = tmp_path / "checkout"
            checkout.mkdir()
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_HERMES_PYTHON=str(hermes),
                    PFY_HERMES_CHECKOUT=str(checkout),
                    PFY_HERMES_HOME=str(tmp_path / "home"),
                    PFY_BOT_TIMEOUT="1",
                ),
                timeout=10,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("timeout", proc.stdout)
            self.assertTrue(pid_file.exists())
            pid = int(pid_file.read_text(encoding="utf-8"))
            alive = True
            try:
                os.kill(pid, 0)
            except OSError:
                alive = False
            self.assertFalse(alive)

    def test_real_hermes_home_is_refused(self):
        proc = self._run(
            "hello",
            self._env(
                PFY_BOT_INTERFACE="hermes",
                PFY_HERMES_HOME=str(Path.home() / ".hermes"),
            ),
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("under ~/.hermes", proc.stdout + proc.stderr)
        self.assertNotIn("install.sh", proc.stdout + proc.stderr)

    def test_driver_missing_checkout_writes_an_error_and_does_not_call_out(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out = tmp_path / "out.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(DRIVER),
                    "--prompt",
                    "hello",
                    "--out",
                    str(out),
                    "--base-url",
                    "http://127.0.0.1:9/v1",
                    "--model",
                    "qwen3.6:35b",
                    "--reasoning",
                    "off",
                    "--home",
                    str(tmp_path / "home"),
                    "--checkout",
                    str(tmp_path / "no-checkout"),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=ROOT,
            )
            self.assertEqual(proc.returncode, 1, proc.stderr)
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertFalse(payload["ok"])
        self.assertIn("missing", payload["error"])


if __name__ == "__main__":
    unittest.main()
