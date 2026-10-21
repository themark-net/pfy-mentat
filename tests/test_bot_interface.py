"""Bot interface fail and recover. Fake processes, a local HTTP probe, and one E2E
run of the real opencode binary against an in-process stub server. No Ollama."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
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


def _stdin_script(stamp: Path) -> str:
    """Fake opencode that reads stdin to EOF, like a CLI that sees a non-tty pipe."""
    return (
        "#!/bin/sh\n"
        "cat > /dev/null\n"
        f"printf '%s\\n' stdin-closed > {json.dumps(str(stamp))}\n"
        "echo opencode-ok\n"
        "exit 0\n"
    )


def _env_script(dump: Path) -> str:
    """Fake opencode that records its cwd, env, and argv as JSON."""
    return (
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        f"open({json.dumps(str(dump))}, 'w', encoding='utf-8').write(json.dumps("
        "{'cwd': os.getcwd(), 'env': dict(os.environ), 'argv': sys.argv[1:]}))\n"
        "print('opencode-ok')\n"
    )


_STUB_RUN_AGENT = """
import json, os
from pathlib import Path


class AIAgent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        home = Path(os.environ["HERMES_HOME"])
        record = {key: value for key, value in kwargs.items() if key != "request_overrides"}
        (home / "agent-started.json").write_text(json.dumps(record, default=str), encoding="utf-8")

    def run_conversation(self, user_message):
        if user_message == "boom":
            raise RuntimeError("stub failure")
        return {"final_response": "stub-hermes-ok", "messages": []}
"""


def _stub_hermes(tmp_path: Path) -> tuple[Path, Path]:
    """A present Hermes checkout whose AIAgent records that it started. Python is this interpreter."""
    checkout = tmp_path / "hermes-checkout"
    checkout.mkdir()
    (checkout / "run_agent.py").write_text(_STUB_RUN_AGENT, encoding="utf-8")
    home = tmp_path / "hermes-home"
    return checkout, home


class _ChatStub(BaseHTTPRequestHandler):
    """OpenAI-compatible enough for one opencode turn. Records each request."""

    protocol_version = "HTTP/1.1"
    seen: list = []

    def _send(self, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        self.seen.append(("GET", self.path, None))
        self._send(b'{"models":[],"data":[]}')

    def do_POST(self):  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            body = json.loads(raw)
        except ValueError:
            body = {}
        model = body.get("model")
        self.seen.append(("POST", self.path, model))
        delta = {"role": "assistant", "content": "stub-reply-ok"}
        if body.get("stream"):
            chunks = [
                {"id": "c1", "object": "chat.completion.chunk", "created": 1, "model": model,
                 "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                {"id": "c1", "object": "chat.completion.chunk", "created": 1, "model": model,
                 "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
            ]
            data = b"".join(b"data: " + json.dumps(c).encode() + b"\n\n" for c in chunks)
            self._send(data + b"data: [DONE]\n\n", "text/event-stream")
            return
        reply = {"id": "c1", "object": "chat.completion", "created": 1, "model": model,
                 "choices": [{"index": 0, "message": delta, "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
        self._send(json.dumps(reply).encode())

    def log_message(self, fmt, *args):
        return


def _real_opencode() -> str:
    explicit = (os.environ.get("PFY_BOT_OPENCODE") or "").strip()
    if explicit and Path(explicit).exists():
        return explicit
    return shutil.which("opencode") or ""


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
        self.assertIn("notice: PFY_BOT_INTERFACE=hermes was requested but Hermes is missing", proc.stderr)
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

    def test_open_stdin_pipe_does_not_hang_the_child(self):
        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            opencode = tmp_path / "opencode"
            seen = tmp_path / "stdin-stamp"
            _fake(opencode, _stdin_script(seen))
            env = self._env(
                LOCAL_OPENAI_BASE_URL=base,
                PFY_ROOT=str(tmp_path / "root"),
                PFY_BOT_OPENCODE=str(opencode),
                PFY_BOT_TIMEOUT="8",
            )
            started = time.monotonic()
            # stdin is a pipe this test never closes, as under a non-tty caller.
            proc = subprocess.Popen(
                [sys.executable, str(BOT), "hello"],
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=ROOT,
            )
            try:
                stdout, stderr = proc.stdout.read(), proc.stderr.read()
                proc.wait(timeout=20)
            finally:
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    stream.close()
            elapsed = time.monotonic() - started
            self.assertTrue(seen.exists(), stdout + stderr)
        self.assertEqual(proc.returncode, 0, stdout + stderr)
        self.assertNotIn("timeout", stdout)
        self.assertLess(elapsed, 8)

    def test_opencode_child_gets_a_provider_for_the_server_and_no_user_config(self):
        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            opencode = tmp_path / "opencode"
            dump = tmp_path / "dump.json"
            _fake(opencode, _env_script(dump))
            root = tmp_path / "root"
            proc = self._run(
                "hello",
                self._env(
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_ROOT=str(root),
                    PFY_BOT_OPENCODE=str(opencode),
                    PFY_BOT_MODEL="some-model:7b",
                    OPENCODE_CONFIG="/nonexistent/user/opencode.json",
                    OPENCODE_CONFIG_CONTENT='{"model": "anthropic/x"}',
                ),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            seen = json.loads(dump.read_text(encoding="utf-8"))
            env = seen["env"]
            config = json.loads(Path(env["OPENCODE_CONFIG"]).read_text(encoding="utf-8"))
            work = (root / "tmp" / "bot-interface").resolve()
        self.assertIn("--model", seen["argv"])
        self.assertEqual(seen["argv"][seen["argv"].index("--model") + 1], "ollama/some-model:7b")
        provider = config["provider"]["ollama"]
        self.assertEqual(provider["options"]["baseURL"], base)
        self.assertIn("some-model:7b", provider["models"])
        self.assertEqual(env["OPENCODE_DISABLE_PROJECT_CONFIG"], "1")
        self.assertNotIn("OPENCODE_CONFIG_CONTENT", env)
        for key in ("HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "OPENCODE_CONFIG"):
            self.assertTrue(Path(env[key]).resolve().is_relative_to(work), key)
        self.assertTrue(Path(seen["cwd"]).resolve().is_relative_to(work))
        real_home = Path(os.environ.get("HOME", str(Path.home()))).resolve()
        for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
            self.assertNotEqual(Path(env[key]).resolve().parent, real_home, key)

    @unittest.skipUnless(_real_opencode(), "opencode binary not found on PATH or PFY_BOT_OPENCODE")
    def test_real_opencode_resolves_the_provider_and_reaches_the_server(self):
        for flag in ("", "hermes"):
            with self.subTest(interface=flag or "default"):
                _ChatStub.seen = []
                server = ThreadingHTTPServer(("127.0.0.1", 0), _ChatStub)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    base = f"http://127.0.0.1:{server.server_address[1]}/v1"
                    with tempfile.TemporaryDirectory() as tmp:
                        tmp_path = Path(tmp)
                        extra = {}
                        if flag:
                            extra = {
                                "PFY_BOT_INTERFACE": flag,
                                "PFY_HERMES_PYTHON": str(tmp_path / "missing-python"),
                                "PFY_HERMES_CHECKOUT": str(tmp_path / "missing-checkout"),
                                "PFY_HERMES_HOME": str(tmp_path / "hermes-home"),
                            }
                        proc = self._run(
                            "Reply with one word.",
                            self._env(
                                LOCAL_OPENAI_BASE_URL=base,
                                PFY_ROOT=str(tmp_path / "root"),
                                PFY_BOT_OPENCODE=_real_opencode(),
                                PFY_BOT_MODEL="pfy-stub-model",
                                PFY_BOT_TIMEOUT="90",
                                **extra,
                            ),
                            timeout=120,
                        )
                finally:
                    server.shutdown()
                    server.server_close()
                out = proc.stdout + proc.stderr
                self.assertNotIn("ProviderModelNotFoundError", out)
                self.assertNotIn("Provider not found", out)
                self.assertEqual(proc.returncode, 0, out)
                posts = [row for row in _ChatStub.seen if row[0] == "POST"]
                self.assertTrue(posts, out)
                self.assertTrue(all(path == "/v1/chat/completions" for _, path, _ in posts), posts)
                self.assertIn("pfy-stub-model", [model for _, _, model in posts])
                self.assertIn("stub-reply-ok", proc.stdout)
                if flag:
                    self.assertIn("falling back to opencode", proc.stdout)

    def _stub_env(self, tmp_path: Path, base: str, **extra):
        checkout, home = _stub_hermes(tmp_path)
        opencode = tmp_path / "opencode"
        _fake(opencode, _opencode_script(tmp_path / "opencode-stamp"))
        env = self._env(
            LOCAL_OPENAI_BASE_URL=base,
            PFY_ROOT=str(tmp_path / "root"),
            PFY_HERMES_PYTHON=sys.executable,
            PFY_HERMES_CHECKOUT=str(checkout),
            PFY_HERMES_HOME=str(home),
            PFY_BOT_OPENCODE=str(opencode),
        )
        env.pop("PFY_BOT_INTERFACE", None)
        env.update(extra)
        return env, home / "agent-started.json", tmp_path / "opencode-stamp"

    def test_default_off_never_starts_a_present_hermes(self):
        base = self._server()
        # Positive control: the same stub is found and started when the flag is hermes.
        with tempfile.TemporaryDirectory() as tmp:
            env, started, oc = self._stub_env(Path(tmp), base, PFY_BOT_INTERFACE="hermes")
            proc = self._run("hello", env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(started.exists(), proc.stdout + proc.stderr)
            self.assertFalse(oc.exists())
            self.assertIn("stub-hermes-ok", proc.stdout)
        for label, value in (("unset", None), ("empty", ""), ("blank", "  "), ("off", "off"), ("opencode", "OpenCode")):
            with self.subTest(flag=label), tempfile.TemporaryDirectory() as tmp:
                env, started, oc = self._stub_env(Path(tmp), base)
                if value is not None:
                    env["PFY_BOT_INTERFACE"] = value
                proc = self._run("hello", env)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertFalse(started.exists(), label)
                self.assertTrue(oc.exists(), label)
                self.assertIn("bot interface: opencode", proc.stdout)
                self.assertNotIn("bot interface: hermes", proc.stdout)
                self.assertNotIn("Hermes checkout", proc.stdout)

    def test_hermes_driver_runs_with_no_toolsets(self):
        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            env, started, _oc = self._stub_env(Path(tmp), base, PFY_BOT_INTERFACE="hermes")
            proc = self._run("hello", env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            kwargs = json.loads(started.read_text(encoding="utf-8"))
            config = (started.parent / "config.yaml").read_text(encoding="utf-8")
        self.assertEqual(kwargs["enabled_toolsets"], [])
        self.assertEqual(kwargs["base_url"], base)
        self.assertIn("mode: off", config)

    def test_hermes_driver_failure_is_a_failure(self):
        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            env, started, oc = self._stub_env(Path(tmp), base, PFY_BOT_INTERFACE="hermes")
            proc = self._run("boom", env)
            self.assertTrue(started.exists())
            self.assertFalse(oc.exists())
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("FAIL: Hermes driver Hermes run failed: RuntimeError", proc.stdout)

    def test_bad_flag_values_exit_2_and_start_nothing(self):
        base = self._server()
        for value in ("yes", "1", "hermes;rm -rf x", "h\u00e9rmes"):
            with self.subTest(flag=value), tempfile.TemporaryDirectory() as tmp:
                env, started, oc = self._stub_env(Path(tmp), base, PFY_BOT_INTERFACE=value)
                proc = self._run("hello", env)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("PFY_BOT_INTERFACE must be opencode or hermes", proc.stdout)
                self.assertFalse(started.exists())
                self.assertFalse(oc.exists())
        with tempfile.TemporaryDirectory() as tmp:
            env, started, _oc = self._stub_env(Path(tmp), base, PFY_BOT_INTERFACE=" HERMES ")
            proc = self._run("hello", env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(started.exists())

    def test_bad_reasoning_and_empty_prompt_exit_2_and_start_nothing(self):
        base = self._server()
        cases = (("hello", {"PFY_BOT_REASONING": "maybe"}, "PFY_BOT_REASONING must be off or on"), ("   ", {}, "prompt is empty"))
        for prompt, extra, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as tmp:
                env, started, oc = self._stub_env(Path(tmp), base, **extra)
                proc = self._run(prompt, env)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(message, proc.stdout)
                self.assertFalse(started.exists())
                self.assertFalse(oc.exists())

    def test_opencode_nonzero_exit_is_a_failure(self):
        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            opencode = tmp_path / "opencode"
            _fake(opencode, "#!/bin/sh\necho broken >&2\nexit 7\n")
            proc = self._run(
                "hello",
                self._env(LOCAL_OPENAI_BASE_URL=base, PFY_ROOT=str(tmp_path / "root"), PFY_BOT_OPENCODE=str(opencode)),
            )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("FAIL: opencode exited 7", proc.stdout)
        self.assertIn("broken", proc.stdout)

    def test_root_base_url_gets_v1(self):
        base = self._server()
        root_form = base[: -len("/v1")] + "/"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            opencode = tmp_path / "opencode"
            dump = tmp_path / "dump.json"
            _fake(opencode, _env_script(dump))
            proc = self._run(
                "hello",
                self._env(LOCAL_OPENAI_BASE_URL=root_form, PFY_ROOT=str(tmp_path / "root"), PFY_BOT_OPENCODE=str(opencode)),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            env = json.loads(dump.read_text(encoding="utf-8"))["env"]
            config = json.loads(Path(env["OPENCODE_CONFIG"]).read_text(encoding="utf-8"))
        self.assertIn(f"endpoint: {base}\n", proc.stdout)
        self.assertEqual(config["provider"]["ollama"]["options"]["baseURL"], base)

    def test_real_hermes_home_is_refused(self):
        base = self._server()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            checkout, _home = _stub_hermes(tmp_path)
            driver = tmp_path / "driver.py"
            pid = tmp_path / "driver-started"
            _fake(driver, _sleep_script(pid))
            proc = self._run(
                "hello",
                self._env(
                    PFY_BOT_INTERFACE="hermes",
                    LOCAL_OPENAI_BASE_URL=base,
                    PFY_ROOT=str(tmp_path / "root"),
                    PFY_HERMES_PYTHON=sys.executable,
                    PFY_HERMES_CHECKOUT=str(checkout),
                    PFY_BOT_DRIVER=str(driver),
                    PFY_HERMES_HOME=str(Path.home() / ".hermes"),
                ),
            )
            self.assertFalse(pid.exists())
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("PFY_HERMES_HOME resolves under ~/.hermes", proc.stdout + proc.stderr)
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
