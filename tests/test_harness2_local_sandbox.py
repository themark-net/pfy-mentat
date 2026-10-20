#!/usr/bin/env python3
"""Behavior tests for the harness2-local network sandbox.

Each test runs examples/harness2-local/sandbox.py (or sbun) as a subprocess.
Nothing here loads a model. Stub HTTP servers and stub binaries stand in.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import textwrap
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SANDBOX = REPO / "examples" / "harness2-local" / "sandbox.py"
SBUN = REPO / "examples" / "harness2-local" / "sbun"
PY = sys.executable


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def _read(self) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _send(self, payload: bytes, content_type: str = "application/json") -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        self.server.hits.append(("GET", self.path, b""))
        self._send(b'{"object":"list","data":[{"id":"qwen3.6-35b"}]}')

    def do_POST(self) -> None:  # noqa: N802
        raw = self._read()
        self.server.hits.append(("POST", self.path, raw))
        payload = json.dumps({
            "id": "stub",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "pong"},
                "finish_reason": "stop",
            }],
        }).encode()
        self._send(payload)

    def log_message(self, fmt: str, *args) -> None:
        return


def serve() -> tuple[ThreadingHTTPServer, int]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.hits = []
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


class Box:
    """A private HOME and worktree under the worktree tmp dir, never under /tmp."""

    def __init__(self, name: str):
        # Short on purpose: unix socket paths must fit sun_path (107 bytes).
        self.root = REPO / "tmp" / "s" / name[:12]
        if self.root.exists():
            subprocess.run(["chmod", "-R", "u+rwX", "--", str(self.root)], check=False)
            shutil.rmtree(self.root)
        self.home = self.root / "h"
        self.py = self.home / ".local" / "share" / "uv" / "python" / "cpython-test"
        self.wt = self.home / "wt"
        self.harness = self.wt / "tmp" / "harness2"
        self.runs = self.wt / "tmp" / "harness2-runs"
        self.state = self.wt / "tmp" / "state"
        self.py.mkdir(parents=True)
        (self.harness / ".venv" / "bin").mkdir(parents=True)
        (self.runs / "tmp").mkdir(parents=True)
        (self.state / "r").mkdir(parents=True)
        (self.state / "bin").mkdir(parents=True)
        self.n = 0

    def close(self) -> None:
        if self.root.exists():
            subprocess.run(["chmod", "-R", "u+rwX", "--", str(self.root)], check=False)
            shutil.rmtree(self.root, ignore_errors=True)

    def ws(self, runs: Path | None = None) -> Path:
        self.n += 1
        root = (runs or self.runs) / "tmp"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"w{self.n}"
        path.mkdir()
        return path

    def env(self, **extra: str) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["HARNESS2_W"] = str(self.wt)
        env.update(extra)
        return env

    def args(self, ws: Path, cmd: list[str], *, runs: Path | None = None,
             extra: list[str] | None = None) -> list[str]:
        out = [
            PY, str(SANDBOX),
            "--harness", str(self.harness),
            "--runs", str(runs or self.runs),
            "--state", str(self.state),
            "--py312", str(self.py),
            "--ws", str(ws),
        ]
        if extra:
            out += extra
        return out + ["--", *cmd]


def run(args: list[str], env: dict[str, str], timeout: float = 90) -> subprocess.CompletedProcess:
    return subprocess.run(args, env=env, capture_output=True, text=True, timeout=timeout)


def write_script(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


class SandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.box = Box(f"{os.getpid():x}"[-6:] + self._testMethodName[:4])

    def tearDown(self) -> None:
        self.box.close()

    def test_child_runs_and_git_rg_resolve(self) -> None:
        ws = self.box.ws()
        script = ws / "child.py"
        write_script(script, f"""
            import shutil, pathlib
            pathlib.Path({str(ws / "marker")!r}).write_text("ran")
            pathlib.Path({str(ws / "tools")!r}).write_text(
                (shutil.which("git") or "") + "\\n" + (shutil.which("rg") or "")
            )
        """)
        proc = run(self.box.args(ws, [PY, str(script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        git, rg = (ws / "tools").read_text().splitlines()
        self.assertTrue(git.endswith("/git"), git)
        self.assertTrue(rg.endswith("/rg"), rg)

    def test_bwrap_missing_does_not_run_child(self) -> None:
        ws = self.box.ws()
        empty = self.box.root / "nobwrap"
        empty.mkdir()
        env = self.box.env(PATH=str(empty))
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), env)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("bwrap required", proc.stderr)
        self.assertFalse((ws / "marker").exists())

    def test_allow_list_forwards_only_A(self) -> None:
        http_a, port_a = serve()
        http_b, port_b = serve()
        http_c, port_c = serve()
        self.addCleanup(http_a.shutdown)
        self.addCleanup(http_b.shutdown)
        self.addCleanup(http_c.shutdown)
        ws = self.box.ws()
        script = ws / "child.py"
        write_script(script, f"""
            import json, pathlib, socket, urllib.request
            ws = pathlib.Path({str(ws)!r})
            ws.joinpath("marker").write_text("ran")
            out = {{}}
            def hit(name, port):
                body = json.dumps({{"model": "qwen3.6-35b", "temperature": 0, "seed": 230}}).encode()
                req = urllib.request.Request(
                    f"http://127.0.0.1:{{port}}/v1/chat/completions", data=body, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        out[name] = resp.status
                except Exception as exc:
                    out[name] = type(exc).__name__
            hit("A", {port_a})
            hit("B", {port_b})
            try:
                socket.create_connection(("127.0.0.1", {port_c}), timeout=2).close()
                out["C"] = "open"
            except Exception as exc:
                out["C"] = type(exc).__name__
            try:
                socket.create_connection(("1.1.1.1", 443), timeout=2).close()
                out["net"] = "open"
            except Exception as exc:
                out["net"] = type(exc).__name__
            ws.joinpath("out.json").write_text(json.dumps(out))
        """)
        proc = run(self.box.args(ws, [PY, str(script)], extra=[
            "--expose", f"{port_a},{port_b}", "--allow", str(port_a),
        ]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        got = json.loads((ws / "out.json").read_text())
        self.assertEqual(got["A"], 200, got)
        self.assertNotEqual(got["B"], 200, got)
        self.assertNotEqual(got["C"], "open", got)
        self.assertNotEqual(got["net"], "open", got)
        log = (self.box.state / "relay.log").read_text(encoding="utf-8")
        self.assertIn("temperature: 0", log)
        self.assertIn("seed: 230", log)
        self.assertIn(f"denied port {port_b}", log)
        self.assertTrue(http_a.hits)
        self.assertFalse(http_b.hits)
        self.assertFalse(http_c.hits)

    def test_env_allow_list_drops_secrets_and_open_code_overrides(self) -> None:
        ws = self.box.ws()
        script = ws / "child.py"
        write_script(script, f"""
            import json, os, pathlib
            pathlib.Path({str(ws / "marker")!r}).write_text("ran")
            pathlib.Path({str(ws / "env.json")!r}).write_text(json.dumps(dict(os.environ)))
        """)
        env = self.box.env(
            FOO_TOKEN="t",
            BAR_SECRET="s",
            BAZ_KEY="k",
            GITHUB_PAT="p",
            AWS_CREDENTIALS="c",
            X_PASSWD="w",
            TOKEN="bare",
            SOME_UNLISTED_VAR="nope",
            DBUS_SESSION_BUS_ADDRESS="unix:path=/run/bus",
            SSH_AUTH_SOCK="/tmp/ssh",
            XDG_RUNTIME_DIR="/run/user/1",
            DOCKER_HOST="unix:///var/run/docker.sock",
            HARNESS2_RUNS_DIR=str(self.box.runs),
            OPENCODE_CONFIG="/host/bogus.json",
            OPENCODE_CONFIG_DIR="/host/dir",
            OPENCODE_CONFIG_CONTENT="nope",
            OPENCODE_TEST_MANAGED_CONFIG_DIR="/host/managed",
            OPENCODE_FOO="nope",
            OPENCODE_PERMISSION='{"external_directory":{"*":"deny"}}',
            OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX="4096",
            OPENCODE_DISABLE_MODELS_FETCH="1",
        )
        proc = run(self.box.args(ws, [PY, str(script)]), env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        child = json.loads((ws / "env.json").read_text())
        for name in (
            "FOO_TOKEN", "BAR_SECRET", "BAZ_KEY", "GITHUB_PAT", "AWS_CREDENTIALS",
            "X_PASSWD", "TOKEN", "SOME_UNLISTED_VAR", "DBUS_SESSION_BUS_ADDRESS",
            "SSH_AUTH_SOCK", "XDG_RUNTIME_DIR", "DOCKER_HOST", "OPENCODE_CONFIG_DIR",
            "OPENCODE_CONFIG_CONTENT", "OPENCODE_TEST_MANAGED_CONFIG_DIR", "OPENCODE_FOO",
        ):
            self.assertNotIn(name, child, name)
        self.assertEqual(child.get("HARNESS2_RUNS_DIR"), str(self.box.runs))
        self.assertEqual(child.get("OPENCODE_CONFIG"), str(self.box.state / "opencode.json"))
        self.assertEqual(child.get("OPENCODE_PERMISSION"), env["OPENCODE_PERMISSION"])
        self.assertEqual(child.get("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"), "4096")
        self.assertEqual(child.get("OPENCODE_DISABLE_MODELS_FETCH"), "1")
        self.assertTrue(child.get("XDG_CONFIG_HOME", "").endswith("/.config"))
        self.assertNotIn(str(self.box.state), child.get("XDG_CONFIG_HOME", ""))

    def test_canary_home_is_unreadable(self) -> None:
        token = "canary-" + str(os.getpid())
        (self.box.home / "canary.txt").write_text(token)
        ssh = self.box.home / ".ssh"
        ssh.mkdir()
        (ssh / "id_test").write_text(token)
        self._git_worktree()
        ws = self.box.ws()
        script = ws / "child.py"
        write_script(script, f"""
            import os, pathlib
            ws = pathlib.Path({str(ws)!r})
            home = pathlib.Path(os.environ["HOME"])
            ws.joinpath("marker").write_text("ran")
            lines = []
            for rel in ("canary.txt", ".ssh/id_test"):
                path = home / rel
                try:
                    lines.append("READ " + path.read_text())
                except OSError as exc:
                    lines.append("ERR " + rel + " " + str(exc.errno))
            listing = []
            try:
                listing = os.listdir(home)
            except OSError as exc:
                listing = ["LSERR", str(exc.errno)]
            ws.joinpath("reads").write_text("\\n".join(lines + ["LS"] + listing))
        """)
        proc = run(self.box.args(ws, [PY, str(script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, "invalid run: " + proc.stderr)
        self.assertTrue((ws / "marker").exists(), "invalid run: no marker")
        text = (ws / "reads").read_text()
        self.assertNotIn(token, text)
        self.assertNotIn(token, proc.stdout + proc.stderr)
        self.assertNotIn("canary.txt", text.split("LS", 1)[-1])
        for path in ws.rglob("*"):
            if path.is_file():
                self.assertNotIn(token, path.read_text(errors="replace"))

    def test_hidden_unix_sockets_and_live_paths(self) -> None:
        fake = self.box.state / "fake-run"
        (fake / "user" / "1000").mkdir(parents=True)
        socks = [fake / "stub.sock", fake / "user" / "1000" / "bus"]
        listeners = []
        for path in socks:
            srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            if path.exists():
                path.unlink()
            srv.bind(str(path))
            srv.listen(4)
            listeners.append(srv)
            self.addCleanup(srv.close)
        ws = self.box.ws()
        uid = os.getuid()
        script = ws / "child.py"
        write_script(script, f"""
            import os, pathlib, socket
            ws = pathlib.Path({str(ws)!r})
            ws.joinpath("marker").write_text("ran")
            lines = []
            for path in { [str(p) for p in socks]!r }:
                try:
                    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    c.settimeout(2)
                    c.connect(path)
                    lines.append("OPEN " + path)
                except OSError as exc:
                    lines.append("ERR " + path + " " + str(exc.errno))
            for path in ("/run/docker.sock", "/var/run/docker.sock",
                         "/run/user/{uid}/bus",
                         os.path.expanduser("~/.ssh"),
                         os.path.expanduser("~/.config/gh")):
                lines.append(("YES " if os.path.exists(path) else "NO ") + path)
            ws.joinpath("out").write_text("\\n".join(lines))
        """)
        proc = run(self.box.args(ws, [PY, str(script)], extra=["--hide-dir", str(fake)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        text = (ws / "out").read_text()
        self.assertNotIn("OPEN ", text, text)
        self.assertIn("NO /run/docker.sock", text)
        self.assertIn("NO /var/run/docker.sock", text)
        self.assertIn(f"NO /run/user/{uid}/bus", text)
        for srv, path in zip(listeners, socks):
            host = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            host.settimeout(2)
            host.connect(str(path))
            host.close()

    def test_answer_files_and_id_map_are_absent_inside(self) -> None:
        cases = self.box.wt / "data" / "decision-gates"
        cases.mkdir(parents=True)
        (cases / "laya-trial.cases.v0.json").write_text('{"cases":[]}')
        split = self.box.wt / "examples" / "harness2-local"
        split.mkdir(parents=True)
        (split / "split.v0.json").write_text("{}")
        host_only = self.box.wt / "tmp" / "host-only"
        host_only.mkdir(parents=True)
        (host_only / "id-map.json").write_text('{"a":"t01"}')
        ws = self.box.ws()
        paths = [
            str(cases / "laya-trial.cases.v0.json"),
            str(split / "split.v0.json"),
            str(host_only / "id-map.json"),
            str(self.box.state / "id-map.json"),
        ]
        script = ws / "child.py"
        write_script(script, f"""
            import os, pathlib
            ws = pathlib.Path({str(ws)!r})
            ws.joinpath("marker").write_text("ran")
            lines = []
            for path in {paths!r}:
                lines.append(("YES " if os.path.exists(path) else "NO ") + path)
            ws.joinpath("out").write_text("\\n".join(lines))
        """)
        proc = run(self.box.args(ws, [PY, str(script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        for line in (ws / "out").read_text().splitlines():
            self.assertTrue(line.startswith("NO "), line)

    def test_socket_in_runs_blocks_before_child(self) -> None:
        ws = self.box.ws()
        sock_path = self.box.runs / "evil.sock"
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(sock_path))
        srv.listen(1)
        self.addCleanup(srv.close)
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sandbox-socket", proc.stderr)
        self.assertIn(str(sock_path), proc.stderr)
        self.assertFalse((ws / "marker").exists())

    def test_stub_find_error_is_fail_closed(self) -> None:
        write_script(self.box.harness / ".venv" / "bin" / "find", """
            #!/bin/sh
            echo "find: stub error" >&2
            exit 1
        """)
        ws = self.box.ws()
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sandbox-socket rc=1", proc.stderr)
        self.assertIn("mount=", proc.stderr)
        self.assertFalse((ws / "marker").exists())

    def test_stub_find_timeout_names_the_mount(self) -> None:
        write_script(self.box.harness / ".venv" / "bin" / "find", """
            #!/bin/sh
            sleep 30
        """)
        ws = self.box.ws()
        t0 = time.time()
        proc = run(self.box.args(
            ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"],
            extra=["--mount-timeout", "2", "--preflight-cap", "30"],
        ), self.box.env(), timeout=20)
        self.assertLess(time.time() - t0, 15)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sandbox-socket timeout", proc.stderr)
        self.assertFalse((ws / "marker").exists())

    def test_unreadable_dir_and_clean_etc_layout(self) -> None:
        blocked = self.box.runs / "locked"
        blocked.mkdir()
        os.chmod(blocked, 0o100)
        ws = self.box.ws()
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sandbox-socket rc=", proc.stderr)
        self.assertFalse((ws / "marker").exists())
        os.chmod(blocked, 0o700)
        blocked.rmdir()
        private = self._root_0700()
        self.assertIsNotNone(private, "no root-owned 0700 dir under /etc or /usr to prove the prune")
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        self.assertFalse(Path("/etc/opencode").exists())

    def test_socket_outside_state_r_blocks(self) -> None:
        ws = self.box.ws()
        sock_path = self.box.state / "not-relay.sock"
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(sock_path))
        srv.listen(1)
        self.addCleanup(srv.close)
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sandbox-socket", proc.stderr)
        self.assertIn(str(sock_path), proc.stderr)
        self.assertFalse((ws / "marker").exists())

    def test_owned_000_blocks_then_recovers(self) -> None:
        ws = self.box.ws()
        hidden = ws / "hidden"
        hidden.mkdir()
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(hidden / "l.sock"))
        srv.listen(4)
        srv.settimeout(0.2)
        got: list[int] = []
        stop = threading.Event()

        def accept() -> None:
            while not stop.is_set():
                try:
                    conn, _ = srv.accept()
                    got.append(1)
                    conn.close()
                except socket.timeout:
                    pass

        threading.Thread(target=accept, daemon=True).start()
        os.chmod(hidden, 0)
        self.addCleanup(srv.close)
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        stop.set()
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sandbox-socket", proc.stderr)
        self.assertFalse((ws / "marker").exists())
        self.assertEqual(got, [])
        os.chmod(hidden, 0o700)
        shutil.rmtree(hidden)
        runs_hidden = self.box.runs / "owned0"
        runs_hidden.mkdir()
        os.chmod(runs_hidden, 0)
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertFalse((ws / "marker").exists())
        os.chmod(runs_hidden, 0o700)
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")

    def test_writes_outside_workspace_are_erofs(self) -> None:
        ws = self.box.ws()
        targets = [
            self.box.state / "opencode.json",
            self.box.state / "bin" / "plant",
            self.box.state / "r" / "plant",
            self.box.state / "plant",
            self.box.runs / "plant",
            self.box.runs / "tmp" / "plant",
        ]
        script = ws / "child.py"
        write_script(script, f"""
            import pathlib
            ws = pathlib.Path({str(ws)!r})
            lines = []
            for path in { [str(p) for p in targets]!r }:
                try:
                    pathlib.Path(path).write_text("x")
                    lines.append("OK " + path)
                except OSError as exc:
                    lines.append("ERR " + str(exc.errno) + " " + path)
            ws.joinpath("marker").write_text("ran")
            ws.joinpath("out").write_text("\\n".join(lines))
        """)
        proc = run(self.box.args(ws, [PY, str(script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        for line in (ws / "out").read_text().splitlines():
            self.assertTrue(line.startswith("ERR "), line)

    def test_host_plants_block_and_shell_cannot_plant_runs(self) -> None:
        httpd, port = serve()
        self.addCleanup(httpd.shutdown)
        ws = self.box.ws()
        targets = {
            "runs-json": self.box.runs / "opencode.json",
            "runs-agents": self.box.runs / "tmp" / "AGENTS.md",
        }
        script = ws / "child.py"
        write_script(script, f"""
            import os, pathlib
            ws = pathlib.Path({str(ws)!r})
            xdg = pathlib.Path(os.environ["XDG_CONFIG_HOME"]) / "opencode" / "AGENTS.md"
            lines = []
            for path in [{str(targets["runs-json"])!r}, {str(targets["runs-agents"])!r}, str(xdg)]:
                try:
                    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
                    pathlib.Path(path).write_text("PLANT-CANARY")
                    lines.append("OK " + path)
                except OSError as exc:
                    lines.append("ERR " + str(exc.errno) + " " + path)
            ws.joinpath("marker").write_text("ran")
            ws.joinpath("out").write_text("\\n".join(lines))
        """)
        proc = run(self.box.args(ws, [PY, str(script)], extra=["--expose", str(port), "--allow", str(port)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (ws / "out").read_text()
        self.assertIn(f"ERR 30 {targets['runs-json']}", text)
        self.assertIn(f"ERR 30 {targets['runs-agents']}", text)
        self.assertFalse(targets["runs-json"].exists())
        self.assertFalse(targets["runs-agents"].exists())
        names = [
            "opencode.json", "opencode.jsonc", "AGENTS.md", "CLAUDE.md", "CONTEXT.md",
        ]
        before = len(httpd.hits)
        for folder in (self.box.runs, self.box.runs / "tmp"):
            for name in names:
                path = folder / name
                path.write_text("plant")
                ws2 = self.box.ws()
                proc = run(self.box.args(
                    ws2, ["/bin/sh", "-c", f"echo ran > {ws2}/marker"],
                    extra=["--expose", str(port), "--allow", str(port)],
                ), self.box.env())
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertIn(f"BLOCKED: opencode-plant {path}", proc.stderr)
                self.assertFalse((ws2 / "marker").exists())
                path.unlink()
            dot = folder / ".opencode"
            dot.mkdir()
            ws2 = self.box.ws()
            proc = run(self.box.args(
                ws2, ["/bin/sh", "-c", f"echo ran > {ws2}/marker"],
                extra=["--expose", str(port), "--allow", str(port)],
            ), self.box.env())
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn(f"BLOCKED: opencode-plant {dot}", proc.stderr)
            self.assertFalse((ws2 / "marker").exists())
            dot.rmdir()
        # The host watchdog probes GET /health. The child never starts, so no POST.
        posts = [hit for hit in httpd.hits[before:] if hit[0] == "POST"]
        self.assertEqual(posts, [])

    def test_sweep_lets_the_next_call_run(self) -> None:
        ws_a = self.box.ws()
        script = ws_a / "child.py"
        write_script(script, f"""
            import os, pathlib
            d = pathlib.Path({str(ws_a)!r}) / "locked"
            d.mkdir()
            os.chmod(d, 0)
            pathlib.Path({str(ws_a / "marker")!r}).write_text("ran")
        """)
        proc = run(self.box.args(ws_a, [PY, str(script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((ws_a / "locked").is_dir())
        mode = (ws_a / "locked").stat().st_mode
        self.assertTrue(mode & stat.S_IRUSR, oct(mode))
        ws_b = self.box.ws()
        proc = run(self.box.args(ws_b, ["/bin/sh", "-c", f"echo ran > {ws_b}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws_b / "marker").read_text().strip(), "ran")

    def test_killed_call_is_swept_by_the_next_launch(self) -> None:
        for killer in ("kill", "timeout"):
            with self.subTest(killer=killer):
                ws_a = self.box.ws()
                script = ws_a / "sleep.py"
                write_script(script, f"""
                    import os, pathlib, time
                    d = pathlib.Path({str(ws_a)!r}) / "locked"
                    d.mkdir()
                    os.chmod(d, 0)
                    pathlib.Path({str(ws_a / "marker")!r}).write_text("ran")
                    time.sleep(30)
                """)
                args = self.box.args(ws_a, [PY, str(script)])
                if killer == "timeout":
                    proc = subprocess.run(
                        ["timeout", "2", *args], env=self.box.env(),
                        capture_output=True, text=True,
                    )
                    self.assertEqual(proc.returncode, 124, proc.stderr)
                else:
                    proc_p = subprocess.Popen(args, env=self.box.env())
                    deadline = time.time() + 20
                    while time.time() < deadline and not (ws_a / "marker").exists():
                        time.sleep(0.05)
                    self.assertTrue((ws_a / "marker").exists())
                    os.kill(proc_p.pid, 9)
                    proc_p.wait(timeout=5)
                self.assertEqual((ws_a / "locked").stat().st_mode & 0o777, 0)
                ws_b = self.box.ws()
                proc_b = run(self.box.args(ws_b, ["/bin/sh", "-c", f"echo ran > {ws_b}/marker"]), self.box.env())
                self.assertEqual(proc_b.returncode, 0, proc_b.stderr)
                self.assertEqual((ws_b / "marker").read_text().strip(), "ran")
                self.assertTrue((ws_a / "locked").stat().st_mode & stat.S_IRUSR)

    def test_sweep_skips_symlinks_and_leaves_the_target(self) -> None:
        target = self.box.wt / "tmp" / "host-only" / "secret"
        target.mkdir(parents=True)
        secret = target / "file"
        secret.write_text("token")
        os.chmod(secret, 0o600)
        sub = target / "sub"
        sub.mkdir()
        os.chmod(sub, 0o700)
        sock_path = target / "s.sock"
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(sock_path))
        srv.listen(1)
        srv.close()
        link = self.box.runs / "tmp" / "leak"
        link.symlink_to(target, target_is_directory=True)
        plain = self.box.runs / "tmp" / "note.txt"
        plain.write_text("keep")
        finished = self.box.runs / "tmp" / "old"
        finished.mkdir()
        (finished / "inner").symlink_to(target, target_is_directory=True)
        locked = finished / "locked"
        locked.mkdir()
        os.chmod(locked, 0)
        ws = self.box.ws()
        (ws / "inner").symlink_to(target, target_is_directory=True)
        record = self.box.root / "sweep-args"
        stub = self.box.root / "bin"
        stub.mkdir()
        for name, real in (("chmod", "/usr/bin/chmod"), ("find", "/usr/bin/find")):
            write_script(stub / name, f"""
                #!/bin/sh
                echo "{name} $*" >> {record}
                exec {real} "$@"
            """)
        env = self.box.env(PATH=f"{stub}{os.pathsep}{os.environ.get('PATH', '')}")
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        self.assertEqual(stat.S_IMODE(secret.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(sub.stat().st_mode), 0o700)
        self.assertEqual(secret.read_text(), "token")
        self.assertTrue(sock_path.exists())
        self.assertTrue(locked.stat().st_mode & stat.S_IRUSR)
        self.assertEqual(plain.read_text(), "keep")
        logged = record.read_text()
        self.assertNotIn(str(link), logged)
        self.assertIn(str(finished), logged)
        self.assertIn(str(ws), logged)
        self.assertIn(f"sweep: skip symlink {link}", proc.stderr)
        self.assertIn(f"sweep: skip non-directory {plain}", proc.stderr)

    def test_second_call_is_blocked_until_the_first_finishes(self) -> None:
        httpd, port = serve()
        self.addCleanup(httpd.shutdown)
        env = self.box.env()
        expose = ["--expose", str(port), "--allow", str(port)]

        def script(ws: Path, sleep_s: int) -> None:
            write_script(ws / "child.py", f"""
                import json, pathlib, time, urllib.request
                time.sleep({sleep_s})
                pathlib.Path({str(ws / "marker")!r}).write_text("ran")
                body = json.dumps({{"model": "qwen3.6-35b", "temperature": 0, "seed": 230}}).encode()
                req = urllib.request.Request(
                    "http://127.0.0.1:{port}/v1/chat/completions", data=body, method="POST")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read()
            """)

        ws_a = self.box.ws()
        script(ws_a, 5)
        proc_a = subprocess.Popen(
            self.box.args(ws_a, [PY, str(ws_a / "child.py")], extra=expose),
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

        def stop_a() -> None:
            if proc_a.poll() is None:
                proc_a.kill()
                try:
                    proc_a.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass

        self.addCleanup(stop_a)
        pidfile = self.box.state / "relay.pid"
        deadline = time.time() + 20
        while time.time() < deadline and not pidfile.exists():
            if proc_a.poll() is not None:
                err = proc_a.communicate()[1]
                self.fail(f"A exited early rc={proc_a.returncode} {err}")
            time.sleep(0.05)
        self.assertTrue(pidfile.exists(), "A never started")

        ws_b = self.box.ws()
        script(ws_b, 0)
        state_b = self.box.wt / "tmp" / "stb"
        proc_b = subprocess.Popen(
            self.box.args(ws_b, [PY, str(ws_b / "child.py")], extra=["--state", str(state_b), *expose]),
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        t0 = time.time()
        try:
            err_b = proc_b.communicate(timeout=1)[1]
        except subprocess.TimeoutExpired:
            time.sleep(1.5)
            marker = (ws_b / "marker").exists()
            proc_b.kill()
            proc_b.wait(timeout=5)
            self.fail(f"B still running after 1s; child_marker={marker}")
        self.assertLess(time.time() - t0, 1.0)
        self.assertEqual(proc_b.returncode, 2, err_b)
        self.assertIn("BLOCKED: call in progress", err_b)
        self.assertFalse((ws_b / "marker").exists())
        self.assertEqual([hit for hit in httpd.hits if hit[0] == "POST"], [])

        err_a = proc_a.communicate(timeout=20)[1]
        self.assertEqual(proc_a.returncode, 0, err_a)
        self.assertEqual((ws_a / "marker").read_text().strip(), "ran")
        self.assertEqual(len([hit for hit in httpd.hits if hit[0] == "POST"]), 1)

        ws_c = self.box.ws()
        script(ws_c, 0)
        proc_c = run(self.box.args(ws_c, [PY, str(ws_c / "child.py")], extra=expose), env)
        self.assertEqual(proc_c.returncode, 0, proc_c.stderr)
        self.assertEqual((ws_c / "marker").read_text().strip(), "ran")
        self.assertEqual(len([hit for hit in httpd.hits if hit[0] == "POST"]), 2)

    def test_sweep_failure_blocks_the_launch(self) -> None:
        stub = self.box.root / "stubs"
        stub.mkdir()
        write_script(stub / "chmod", "#!/bin/sh\nexit 1\n")
        (self.box.runs / "tmp" / "finished").mkdir()
        ws = self.box.ws()
        env = self.box.env(PATH=str(stub) + os.pathsep + os.environ.get("PATH", ""))
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), env)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: sweep failed", proc.stderr)
        self.assertFalse((ws / "marker").exists())

    def test_preflight_cap_records_the_stub_before_the_next_launch(self) -> None:
        ws = self.box.ws()
        record = ws / "find-calls"
        write_script(self.box.harness / ".venv" / "bin" / "find", f"""
            #!/bin/sh
            echo called >> {record}
            sleep 999
        """)
        t0 = time.time()
        proc = run(self.box.args(
            ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"],
            extra=["--preflight-cap", "6", "--mount-timeout", "30"],
        ), self.box.env(), timeout=20)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 12, proc.stderr)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED: preflight cap", proc.stderr)
        self.assertTrue(record.exists(), "stub find never ran")
        self.assertFalse((ws / "marker").exists())
        record.unlink()
        (self.box.harness / ".venv" / "bin" / "find").unlink()
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")

    def test_heldout_runs_are_not_visible_to_training(self) -> None:
        held_root = self.box.wt / "tmp" / "heldout-runs" / "a1"
        (held_root / "tmp").mkdir(parents=True)
        train_ws = self.box.ws()
        held_ws = self.box.ws(held_root)
        opaque = "heldout-opaque-t17"
        train_script = train_ws / "child.py"
        write_script(train_script, f"""
            import os, pathlib
            ws = pathlib.Path({str(train_ws)!r})
            ws.joinpath("marker").write_text("ran")
            ws.joinpath("seen").write_text("yes" if os.path.exists({str(self.box.wt / "tmp" / "heldout-runs")!r}) else "no")
        """)
        proc = run(self.box.args(train_ws, [PY, str(train_script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((train_ws / "seen").read_text(), "no")
        held_script = held_ws / "child.py"
        write_script(held_script, f"""
            import os, pathlib
            ws = pathlib.Path({str(held_ws)!r})
            ws.joinpath("marker").write_text({opaque!r})
            ws.joinpath("seen").write_text(
                "yes" if os.path.exists({str(self.box.runs)!r}) else "no")
        """)
        proc = run(self.box.args(
            held_ws, [PY, str(held_script)], runs=held_root, extra=["--heldout", "a1"],
        ), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((held_ws / "seen").read_text(), "no")
        blob = ""
        for path in self.box.runs.rglob("*"):
            if path.is_file():
                blob += path.read_text(errors="replace")
        self.assertNotIn(opaque, blob)

    def test_sbun_closes_stdin(self) -> None:
        ws = self.box.ws()
        # The stub must live on a path the sandbox binds. The harness is read-only
        # inside, which is enough to exec a script that only writes the workspace.
        stub = self.box.harness / "stub-bun"
        write_script(stub, f"""
            #!/bin/sh
            cat >/dev/null
            touch "$1"
        """)
        prefix = self.box.home / ".local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu"
        bindir = prefix / "bin"
        bindir.mkdir(parents=True)
        write_script(bindir / "python3.12", f"""
            #!/bin/sh
            echo {prefix}
        """)
        env = self.box.env(HARNESS2_REAL_BUN=str(stub))
        # The pipe stays open. communicate() would close it and hide a missing redirect.
        proc = subprocess.Popen(
            [str(SBUN), str(ws / "marker"), "--dir", str(ws)],
            env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            rc = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            self.fail("sbun blocked on inherited stdin")
        err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
        self.assertEqual(rc, 0, err)
        self.assertTrue((ws / "marker").exists(), err)

    def test_relay_kill_ends_the_call_and_the_next_call_runs(self) -> None:
        httpd, port = serve()
        self.addCleanup(httpd.shutdown)
        ws = self.box.ws()
        script = ws / "loop.py"
        write_script(script, f"""
            import time, urllib.request, pathlib
            pathlib.Path({str(ws / "marker")!r}).write_text("ran")
            while True:
                try:
                    urllib.request.urlopen("http://127.0.0.1:{port}/health", timeout=2).read()
                except Exception:
                    pass
                time.sleep(2)
        """)
        proc = subprocess.Popen(
            self.box.args(ws, [PY, str(script)], extra=["--expose", str(port), "--allow", str(port)]),
            env=self.box.env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.time() + 20
        while time.time() < deadline and not (ws / "marker").exists():
            time.sleep(0.05)
        self.assertTrue((ws / "marker").exists(), "child never started")
        relay_pid = int((self.box.state / "relay.pid").read_text())
        os.kill(relay_pid, 9)
        try:
            _out, err = proc.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            self.fail("call did not end after the relay died")
        self.assertEqual(proc.returncode, 2, err)
        self.assertIn("relay down", err)
        pgid = int((self.box.state / "call.pgid").read_text())
        with self.assertRaises(ProcessLookupError):
            os.killpg(pgid, 0)
        ws2 = self.box.ws()
        again = run(self.box.args(
            ws2, ["/bin/sh", "-c", f"echo ran > {ws2}/marker"],
            extra=["--expose", str(port), "--allow", str(port)],
        ), self.box.env())
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual((ws2 / "marker").read_text().strip(), "ran")

    def test_preflight_and_real_bwrap_argv_match(self) -> None:
        log = self.box.root / "bwrap-log"
        log.mkdir()
        shim = self.box.root / "path"
        shim.mkdir()
        write_script(shim / "bwrap", f"""
            #!/bin/bash
            n=$(find {log} -maxdepth 1 -type f | wc -l)
            printf '%s\\0' "$@" > {log}/argv-$n
            python3 -c 'import json,os,sys; json.dump(dict(os.environ), open(sys.argv[1],"w"))' {log}/env-$n
            exec /usr/bin/bwrap "$@"
        """)
        ws = self.box.ws()
        env = self.box.env(PATH=str(shim) + os.pathsep + os.environ.get("PATH", ""))
        proc = run(self.box.args(ws, ["/bin/sh", "-c", f"echo ran > {ws}/marker"]), env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((ws / "marker").exists())
        argvs = sorted(log.glob("argv-*"))
        envs = sorted(log.glob("env-*"))
        self.assertEqual(len(argvs), 2, [p.name for p in argvs])
        def load(path: Path) -> list[str]:
            return path.read_bytes().split(b"\0")[:-1]
        a = [p.decode() for p in load(argvs[0])]
        b = [p.decode() for p in load(argvs[1])]
        self.assertIn("--", a)
        self.assertIn("--", b)
        self.assertEqual(a[: a.index("--")], b[: b.index("--")])
        self.assertNotEqual(a[a.index("--") :], b[b.index("--") :])
        self.assertIn("--unshare-net", a)
        self.assertIn("--die-with-parent", a)
        ea = json.loads(envs[0].read_text())
        eb = json.loads(envs[1].read_text())
        ea.pop("_", None)
        eb.pop("_", None)
        keys = sorted(set(ea) | set(eb))
        diffs = [k for k in keys if ea.get(k) != eb.get(k)]
        self.assertEqual(diffs, [], {k: (ea.get(k), eb.get(k)) for k in diffs})

    def test_substrate_preflight_wants_a_path(self) -> None:
        venv = REPO / "tmp" / "harness2" / ".venv" / "bin" / "python"
        if not venv.is_file():
            self.skipTest("stage venv is not present")
        code = r"""
import importlib.util
import pathlib
import sys
sys.path.insert(0, "tmp/harness2")
import harness2.config as config
from harness2.substrate.opencode import OpencodeSubstrate
spec = importlib.util.spec_from_file_location(
    "h2sandbox", "examples/harness2-local/sandbox.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
config.BUN = mod.bun_path()
config.OPENCODE_DIR = pathlib.Path("tmp/harness2/dependencies/opencode")
if not isinstance(config.BUN, pathlib.Path):
    raise SystemExit("BUN is not a Path")
OpencodeSubstrate().preflight()
print("ok")
"""
        proc = subprocess.run([str(venv), "-c", code], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ok", proc.stdout)

    def _git_worktree(self) -> None:
        founder = self.box.home / "founder"
        founder.mkdir()
        (founder / "AGENTS.md").write_text("host agents\n")
        (founder / ".opencode").mkdir()
        (founder / ".opencode" / "note").write_text("host opencode\n")
        env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
        subprocess.run(["git", "init", "-q"], cwd=founder, check=True, env=env)
        subprocess.run(["git", "config", "user.email", "h2@example.com"], cwd=founder, check=True, env=env)
        subprocess.run(["git", "config", "user.name", "h2"], cwd=founder, check=True, env=env)
        subprocess.run(["git", "add", "AGENTS.md", ".opencode"], cwd=founder, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=founder, check=True, env=env)
        if self.box.wt.exists():
            shutil.rmtree(self.box.wt)
        subprocess.run(["git", "worktree", "add", "--detach", str(self.box.wt)], cwd=founder, check=True, env=env)
        (self.box.harness / ".venv" / "bin").mkdir(parents=True)
        (self.box.runs / "tmp").mkdir(parents=True)
        (self.box.state / "r").mkdir(parents=True)
        (self.box.home / ".opencode").mkdir(exist_ok=True)
        (self.box.home / ".config" / "opencode").mkdir(parents=True)
        (self.box.home / ".config" / "opencode" / "AGENTS.md").write_text("home agents\n")

    def test_nimo_shaped_home_hides_host_agents(self) -> None:
        self._git_worktree()
        ws = self.box.ws()
        paths = [
            str(self.box.wt / "AGENTS.md"),
            str(self.box.wt / ".opencode"),
            str(self.box.home / "founder" / "AGENTS.md"),
            str(self.box.home / ".opencode"),
            str(self.box.home / ".config" / "opencode" / "AGENTS.md"),
        ]
        script = ws / "child.py"
        write_script(script, f"""
            import os, pathlib
            ws = pathlib.Path({str(ws)!r})
            ws.joinpath("marker").write_text("ran")
            lines = []
            for path in {paths!r}:
                lines.append(("YES " if os.path.exists(path) else "NO ") + path)
            ws.joinpath("out").write_text("\\n".join(lines))
        """)
        proc = run(self.box.args(ws, [PY, str(script)]), self.box.env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ws / "marker").read_text().strip(), "ran")
        for line in (ws / "out").read_text().splitlines():
            self.assertTrue(line.startswith("NO "), line)
        walk = (self.box.state / "plant-walk.txt").read_text(encoding="utf-8")
        self.assertIn("WALK ", walk)
        self.assertNotIn("BLOCKED: opencode-plant", walk)

    def test_opencode_run_uses_config_model_and_a_host_plant_blocks(self) -> None:
        """Real OpenCode at the pin, stub server, no model weights."""
        harness = REPO / "tmp" / "harness2"
        bun = harness / "dependencies" / "tools" / "node_modules" / ".bin" / "bun"
        oc = harness / "dependencies" / "opencode" / "packages" / "opencode"
        if not bun.is_file() or not (oc / "src" / "index.ts").is_file():
            self.skipTest("staged OpenCode is not present")
        httpd, port = serve()
        self.addCleanup(httpd.shutdown)
        cfg = {
            "$schema": "https://opencode.ai/config.json",
            "provider": {
                "llamacpp": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "llama.cpp (local)",
                    "options": {
                        "baseURL": f"http://127.0.0.1:{port}/v1",
                        "apiKey": "local",
                    },
                    "models": {
                        "qwen3.6-35b": {
                            "name": "qwen3.6-35b",
                            "options": {"temperature": 0, "seed": 230},
                        }
                    },
                }
            },
            "model": "llamacpp/qwen3.6-35b",
        }
        (self.box.state / "opencode.json").write_text(json.dumps(cfg, indent=2) + "\n")
        ws = self.box.ws()
        allow = {"*": "deny", str(ws): "allow", f"{ws}/**": "allow"}
        env = self.box.env(
            OPENCODE_DISABLE_MODELS_FETCH="1",
            OPENCODE_DISABLE_AUTOUPDATE="1",
            OPENCODE_DISABLE_LSP_DOWNLOAD="1",
            OPENCODE_DISABLE_DEFAULT_PLUGINS="1",
            OPENCODE_DISABLE_EXTERNAL_SKILLS="1",
            OPENCODE_DISABLE_CLAUDE_CODE="1",
            OPENCODE_PERMISSION=json.dumps({"external_directory": allow}),
            OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX="4096",
        )
        cmd = [
            PY, str(SANDBOX),
            "--harness", str(harness),
            "--runs", str(self.box.runs),
            "--state", str(self.box.state),
            "--py312", str(self.box.py),
            "--ws", str(ws),
            "--expose", str(port), "--allow", str(port),
            "--",
            str(bun), "run", "--cwd", str(oc), "--conditions=browser", "src/index.ts",
            "run", "Reply with the single word pong.",
            "--dir", str(ws), "--model", "llamacpp/qwen3.6-35b",
            "--title", "t", "--format", "json",
        ]
        proc = subprocess.run(
            cmd, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-800:])
        posts = [hit for hit in httpd.hits if hit[0] == "POST"]
        self.assertTrue(posts, httpd.hits)
        blob = b"".join(hit[2] for hit in posts).decode("utf-8", "replace")
        self.assertIn("qwen3.6-35b", blob)
        self.assertNotIn("PLANT-CANARY", blob)
        self.assertNotIn("PARENT-PLANT", blob)
        log = (self.box.state / "relay.log").read_text(encoding="utf-8")
        self.assertIn("temperature: 0", log)
        self.assertIn("seed: 230", log)
        plant = self.box.runs / "opencode.json"
        plant.write_text('{"model":"llamacpp/PARENT-PLANT"}\n')
        before = len(httpd.hits)
        ws2 = self.box.ws()
        blocked = run(self.box.args(
            ws2, ["/bin/sh", "-c", f"echo ran > {ws2}/marker"],
            extra=["--expose", str(port), "--allow", str(port)],
        ), self.box.env())
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertIn(f"BLOCKED: opencode-plant {plant}", blocked.stderr)
        self.assertFalse((ws2 / "marker").exists())
        later = [hit for hit in httpd.hits[before:] if hit[0] == "POST"]
        self.assertEqual(later, [])
        plant.unlink()

    def _root_0700(self) -> str | None:
        candidates = [
            "/etc/ssl/private",
            "/etc/credstore",
            "/etc/credstore.encrypted",
            "/etc/cups/ssl",
        ]
        for path in candidates:
            if not os.path.isdir(path):
                continue
            st = os.stat(path)
            if st.st_uid == 0 and stat.S_IMODE(st.st_mode) == 0o700:
                return path
        return None


if __name__ == "__main__":
    unittest.main()
