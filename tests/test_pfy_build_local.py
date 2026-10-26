#!/usr/bin/env python3
"""Behavior tests for ./pfy build --local. Stub Ollama and stub opencode only."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "tmp" / "local-build-tests"

STUB = r"""#!/usr/bin/env python3
import json
import os
import signal
import sys
import time
from pathlib import Path

argv = sys.argv[1:]
if "--version" in argv:
    print("stub-opencode 0")
    raise SystemExit(0)
if not argv or argv[0] in ("-h", "--help"):
    print("usage: opencode run --pure --model --variant")
    raise SystemExit(0)
if argv[0] != "run":
    print("stub-opencode")
    raise SystemExit(0)

marker = os.environ.get("PFY_STUB_MARKER")
if marker:
    Path(marker).parent.mkdir(parents=True, exist_ok=True)
    Path(marker).write_text("started\n", encoding="utf-8")
report = os.environ.get("PFY_STUB_REPORT")
if report:
    payload = {
        "home": os.environ.get("HOME"),
        "tmpdir": os.environ.get("TMPDIR"),
        "xdg": {k: os.environ[k] for k in sorted(os.environ) if k.startswith("XDG_")},
        "keys": sorted(os.environ),
        "cwd": os.getcwd(),
    }
    Path(report).write_text(json.dumps(payload), encoding="utf-8")

scenario = os.environ.get("PFY_LOCAL_BUILD_SCENARIO", "noop")
if scenario == "hang":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    child_file = os.environ.get("PFY_STUB_CHILD_PID") or ""
    pid = os.fork()
    if pid == 0:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if child_file:
            Path(child_file).write_text(str(os.getpid()), encoding="utf-8")
        while True:
            time.sleep(0.2)
    if child_file:
        Path(child_file + ".parent").write_text(str(os.getpid()), encoding="utf-8")
    while True:
        time.sleep(0.2)
if scenario == "slow-fix":
    time.sleep(float(os.environ.get("PFY_STUB_SLEEP") or "2"))
    scenario = "fix"

root = Path.cwd()
calc = root / "src" / "calc.py"
test_calc = root / "tests" / "test_calc.py"
if scenario == "fix" and calc.exists():
    calc.write_text(calc.read_text(encoding="utf-8").replace("return a + b + 1", "return a + b"), encoding="utf-8")
elif scenario == "protect" and test_calc.exists():
    test_calc.write_text(test_calc.read_text(encoding="utf-8") + "\n# touched by stub\n", encoding="utf-8")
elif scenario == "worse" and calc.exists():
    calc.write_text("def add(a, b):\n    return a + b + 5\n", encoding="utf-8")
elif scenario == "delete-test" and test_calc.exists():
    test_calc.unlink()
raise SystemExit(0)
"""

TEST_CALC = """\
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.calc import add


class CalcTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(1, 1), 2)
"""

TEST_OTHER = """\
import unittest


class OtherTests(unittest.TestCase):
    def test_true(self):
        self.assertTrue(True)
"""

HELP_GOLDEN = """\
usage: pfy build [-h] [-p PROMPT] [--prompt-file PROMPT_FILE] [--cwd CWD]
                 [--dry-run]

Apply local jev toolset, shadow decision, run grok -p (plain).

options:
  -h, --help            show this help message and exit
  -p, --prompt PROMPT   single-turn prompt for grok -p
  --prompt-file PROMPT_FILE
                        read prompt from file
  --cwd CWD             worktree / working directory for grok and receipt
  --dry-run             plan + shadow only; do not write toolset or exec grok
"""

DRY_GOLDEN = """\
pfy build -p · preamble trimmed · 87 tokens_est (chars/4) · task 1 tokens_est
pfy build -p · skills_bundle bundled_link · 2754571 tokens_est (chars/4)
pfy build -p · toolset apply jev --lane local · dry-run
pfy build -p · decision smoke
pfy build -p · decision route (shadow)
ESCALATE decision · (dry-run shadow)
  verdict: escalate
pfy build -p · grok -p --output-format plain --always-approve
session_id: (none)
usage: turns=(n/a) model_calls=(n/a) total_tokens=(n/a) model=(n/a)
receipt: STAMP/receipt.jsonl
READY pfy build -p · dry-run
"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    def _send(self, code, body):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/tags"):
            self._send(200, {"models": self.server.tags})
        elif self.path.startswith("/api/ps"):
            self._send(200, {"models": self.server.ps})
        elif self.path.startswith("/v1/models"):
            data = [{"id": item.get("name")} for item in self.server.tags if isinstance(item, dict)]
            self._send(200, {"object": "list", "data": data})
        else:
            self._send(200, {})

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            payload = {}
        self.server.posts.append((self.path, payload))
        if "/chat/completions" in self.path:
            self._send(200, {"id": "c", "choices": [{"message": {"role": "assistant", "content": "ok"}}]})
            return
        self._send(200, {"ok": True})


def _serve(tags=None, ps=None):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.tags = list(tags or [{"name": "fixture:small", "size": 1024 ** 3}])
    httpd.ps = list(ps or [])
    httpd.posts = []
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def _unloads(httpd) -> int:
    count = 0
    for _path, payload in httpd.posts:
        if isinstance(payload, dict) and payload.get("keep_alive") in (0, 0.0):
            count += 1
    return count


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def _init_repo(repo: Path, bare: Path) -> None:
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "calc.py").write_text("def add(a, b):\n    return a + b + 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "tests" / "test_calc.py").write_text(TEST_CALC, encoding="utf-8")
    (repo / "tests" / "test_other.py").write_text(TEST_OTHER, encoding="utf-8")
    (repo / ".gitignore").write_text("tmp/\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", str(repo), "init", "-b", "main"], stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "test@example.com"])
    subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "test"])
    subprocess.check_call(["git", "-C", str(repo), "add", "-A"])
    subprocess.check_call(["git", "-C", str(repo), "commit", "-m", "base"], stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "init", "--bare", "-b", "main", str(bare)], stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "-C", str(repo), "remote", "add", "origin", str(bare)])
    subprocess.check_call(["git", "-C", str(repo), "push", "-u", "origin", "main"], stdout=subprocess.DEVNULL)


def _kb(gib: float) -> int:
    return int(round(gib * 1024 * 1024))


def _dead(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _under_repo_tmp(path: Path, repo: Path) -> bool:
    resolved = path.resolve()
    base = (repo / "tmp").resolve()
    return resolved == base or base in resolved.parents


def _is_system_tmp(path: Path) -> bool:
    resolved = path.resolve()
    system_tmp = Path("/tmp").resolve()
    return resolved == system_tmp or system_tmp in resolved.parents


def _norm_dry(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("receipt: ") and "pipelines/dogfood/build/" in line:
            lines.append("receipt: STAMP/receipt.jsonl")
        else:
            lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _branches(repo: Path) -> list[str]:
    text = _git(repo, "branch", "--list", "local/*")
    return [line.strip().lstrip("* ").strip() for line in text.splitlines() if line.strip()]


class LocalBuildTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="case-", dir=SCRATCH))
        self.repo = self.tmp / "repo"
        self.bare = self.tmp / "origin.git"
        self.mem = self.tmp / "meminfo"
        self.marker = self.tmp / "marker"
        self.report = self.tmp / "report.json"
        self.child_pid = self.tmp / "child.pid"
        self.stub = self.tmp / "opencode"
        self.stub.write_text(STUB, encoding="utf-8")
        self.stub.chmod(0o755)
        self.write_mem(40, 8, 8)
        _init_repo(self.repo, self.bare)
        self.httpd = _serve()
        self.port = self.httpd.server_address[1]
        self.head0 = _git(self.repo, "rev-parse", "HEAD").strip()
        self.status0 = _git(self.repo, "status", "--porcelain")
        self.refs0 = subprocess.check_output(["git", "ls-remote", str(self.bare)], text=True)
        self._seq = 0

    def tearDown(self):
        try:
            self.httpd.shutdown()
            self.httpd.server_close()
        except Exception:
            pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_mem(self, available_gib, swap_free_gib, swap_total_gib):
        text = (
            "MemTotal: %d kB\nMemAvailable: %d kB\nSwapTotal: %d kB\nSwapFree: %d kB\n"
            % (_kb(128), _kb(available_gib), _kb(swap_total_gib), _kb(swap_free_gib))
        )
        self.mem.write_text(text, encoding="utf-8")

    def env(self, scenario="fix", **extra):
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("PFY_LOCAL_BUILD_") or key.startswith("PFY_STUB_") or key in (
                "PFY_BOT_OPENCODE",
                "PFY_MEMINFO_FILE",
                "LOCAL_OPENAI_BASE_URL",
                "PFY_LOCAL_BUILD_INJECT_CRASH",
            ):
                env.pop(key, None)
        env.update(
            {
                "PFY_MEMINFO_FILE": str(self.mem),
                "PFY_BOT_OPENCODE": str(self.stub),
                "PFY_LOCAL_BUILD_SCENARIO": scenario,
                "PFY_STUB_MARKER": str(self.marker),
                "PFY_STUB_REPORT": str(self.report),
                "PFY_STUB_CHILD_PID": str(self.child_pid),
                "GITHUB_TOKEN": "ghp_supersecretvalue",
                "AWS_SECRET_ACCESS_KEY": "AKIASECRETVALUE",
                "MY_KEY": "abcdkeyvalue",
                "TMPDIR": str(ROOT / "tmp" / "scratch"),
                "PFY_LOCAL_BUILD_MODEL": "not-the-flag-model:latest",
            }
        )
        env.update(extra)
        return env

    def command(self, scenario, extra=None):
        self._seq += 1
        receipt = self.repo / "tmp" / "receipts" / ("%s-%s" % (scenario, self._seq))
        cmd = [
            str(ROOT / "pfy"),
            "build",
            "--repo",
            str(self.repo),
            "--local",
            "fix add so one plus one is two",
            "--model",
            "fixture:small",
            "--endpoint",
            "http://127.0.0.1:%d/v1" % self.port,
            "--test-cmd",
            "python3 -m unittest discover -s tests -t .",
            "--timeout",
            "30",
            "--test-timeout",
            "30",
            "--min-free-gb",
            "32",
            "--receipt-dir",
            str(receipt),
        ]
        if extra:
            cmd.extend(extra)
        return cmd, receipt

    def run_build(self, scenario="fix", extra=None, env_extra=None, timeout=60):
        if self.marker.exists():
            self.marker.unlink()
        cmd, receipt = self.command(scenario, extra)
        proc = subprocess.run(
            cmd,
            cwd=self.repo,
            env=self.env(scenario, **(env_extra or {})),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return proc, receipt

    def receipt(self, proc, receipt_dir):
        path = receipt_dir / "receipt.json"
        self.assertTrue(path.is_file(), proc.stdout + "\n" + proc.stderr)
        return json.loads(path.read_text(encoding="utf-8"))

    def assert_clean_origin(self):
        self.assertEqual(_git(self.repo, "rev-parse", "HEAD").strip(), self.head0)
        self.assertEqual(_git(self.repo, "status", "--porcelain"), self.status0)
        self.assertEqual(subprocess.check_output(["git", "ls-remote", str(self.bare)], text=True), self.refs0)
        self.assertIn("+ 1", (self.repo / "src" / "calc.py").read_text(encoding="utf-8"))

    def assert_no_commit(self, proc, receipt_dir):
        data = self.receipt(proc, receipt_dir)
        self.assertIsNone(data["branch"])
        self.assertIsNone(data["commit"])
        self.assertEqual(_branches(self.repo), [])
        self.assert_clean_origin()
        return data

    def test_fix_creates_one_commit_and_leaves_the_checkout_alone(self):
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["schema"], "pfy-local-build/1")
        self.assertEqual(data["status"], "PASS")
        self.assertNotEqual(data["tests_before"]["exit"], 0)
        self.assertEqual(data["tests_after"]["exit"], 0)
        self.assertTrue(str(data["worktree"]).startswith(str(self.repo / "tmp") + os.sep))
        self.assertEqual(_unloads(self.httpd), 1)
        self.assertFalse(data["model_was_loaded"])
        self.assertTrue(data["unloaded"])
        self.assertEqual(len(_branches(self.repo)), 1)
        self.assertEqual(data["branch"], _branches(self.repo)[0])
        ahead = _git(self.repo, "rev-list", "--count", "%s..%s" % (self.head0, data["branch"])).strip()
        self.assertEqual(ahead, "1")
        shown = _git(self.repo, "show", "%s:src/calc.py" % data["branch"])
        self.assertIn("return a + b\n", shown)
        self.assertNotIn("+ 1", shown)
        names = _git(self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", data["commit"]).strip().splitlines()
        self.assertEqual(names, ["src/calc.py"])
        author = _git(self.repo, "log", "-1", "--format=%an", data["branch"]).strip()
        self.assertEqual(author, "pfy-local-build")
        message = _git(self.repo, "log", "-1", "--format=%B", data["branch"])
        self.assertIn(data["id"], message)
        self.assertIn("fix add", message)
        self.assert_clean_origin()
        self.assertIn("PASS", proc.stdout)

    def test_no_change_does_not_commit(self):
        proc, receipt = self.run_build("noop")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["status"], "FAIL")
        self.assertEqual(data["reason"], "no-change")

    def test_protected_test_edit_does_not_commit(self):
        proc, receipt = self.run_build("protect", extra=["--protect", "tests/*"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["reason"], "protected-path-changed")
        self.assertIn("tests/test_calc.py", data["files_changed"])

    def test_worse_tests_do_not_commit(self):
        proc, receipt = self.run_build("worse")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["reason"], "tests-failed")

    def test_deleting_a_test_is_a_regression(self):
        proc, receipt = self.run_build("delete-test")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["reason"], "tests-regressed")
        self.assertEqual(data["tests_after"]["exit"], 0)
        self.assertLess(
            (data["tests_after"]["passed"] or 0) + (data["tests_after"]["failed"] or 0) + (data["tests_after"]["errors"] or 0),
            (data["tests_before"]["passed"] or 0) + (data["tests_before"]["failed"] or 0) + (data["tests_before"]["errors"] or 0),
        )

    def test_missing_test_command_does_not_start_the_agent(self):
        proc, receipt = self.run_build("fix", extra=["--test-cmd", "/no/such/pfy-test-cmd"])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["reason"], "test-cmd-failed-to-start")
        self.assertFalse(self.marker.exists())

    def test_hang_is_timeout_and_the_group_is_gone(self):
        started = time.monotonic()
        proc, receipt = self.run_build("hang", extra=["--timeout", "2"], timeout=20)
        elapsed = time.monotonic() - started
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertLess(elapsed, 12)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["status"], "TIMEOUT")
        self.assertEqual(data["reason"], "timeout")
        self.assertEqual(_unloads(self.httpd), 1)
        child = int(self.child_pid.read_text(encoding="utf-8"))
        parent = int(Path(str(self.child_pid) + ".parent").read_text(encoding="utf-8"))
        self.assertTrue(_dead(child))
        self.assertTrue(_dead(parent))

    def test_sigterm_interrupts_and_releases_the_lock(self):
        cmd, receipt = self.command("hang", extra=["--timeout", "30"])
        proc = subprocess.Popen(
            cmd,
            cwd=self.repo,
            env=self.env("hang"),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not self.marker.exists():
            if proc.poll() is not None:
                break
            time.sleep(0.05)
        self.assertTrue(self.marker.exists(), "agent did not start")
        os.kill(proc.pid, signal.SIGTERM)
        try:
            out, err = proc.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            os.kill(proc.pid, signal.SIGKILL)
            out, err = proc.communicate(timeout=5)
            self.fail("runner did not exit after SIGTERM\n%s\n%s" % (out, err))
        self.assertEqual(proc.returncode, 1, (out or "") + (err or ""))
        data = self.receipt(subprocess.CompletedProcess(cmd, proc.returncode, out, err), receipt)
        self.assertEqual(data["reason"], "interrupted")
        self.assertIsNone(data["commit"])
        child = int(self.child_pid.read_text(encoding="utf-8"))
        parent = int(Path(str(self.child_pid) + ".parent").read_text(encoding="utf-8"))
        self.assertTrue(_dead(child))
        self.assertTrue(_dead(parent))
        lock = open(self.repo / "tmp" / "local-build.lock", "a+", encoding="utf-8")
        try:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        finally:
            lock.close()

    def test_low_memory_blocks_and_full_swap_is_not_free(self):
        self.write_mem(10, 0, 64)
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["status"], "BLOCKED")
        self.assertEqual(data["reason"], "mem")
        self.assertIsNone(data["worktree"])
        self.assertFalse(self.marker.exists())
        self.assertEqual(_unloads(self.httpd), 0)

    def test_plenty_of_ram_passes_when_swap_is_full(self):
        self.write_mem(40, 0, 64)
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["mem"]["swap_free_gb"], 0)

    def test_busy_host_does_not_unload_and_recovers(self):
        self.httpd.ps = [{"name": "other:7b"}]
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["reason"], "busy-host")
        self.assertFalse(self.marker.exists())
        self.assertEqual(_unloads(self.httpd), 0)
        self.httpd.ps = []
        self.httpd.posts.clear()
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_unloads(self.httpd), 1)

    def test_model_over_30_gib_is_blocked(self):
        self.httpd.tags = [{"name": "fixture:small", "size": 40 * 1024 ** 3}]
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["reason"], "model-too-big")
        self.assertFalse(self.marker.exists())

    def test_cloud_tag_is_blocked(self):
        self.httpd.tags = [{"name": "deepseek-v4-flash:cloud", "size": 1024}]
        proc, receipt = self.run_build("fix", extra=["--model", "deepseek-v4-flash:cloud"])
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["reason"], "cloud-tag")
        self.assertFalse(self.marker.exists())

    def test_missing_opencode_names_the_next_step_and_recovers(self):
        proc, receipt = self.run_build("fix", env_extra={"PFY_BOT_OPENCODE": str(self.tmp / "missing-opencode")})
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        blob = proc.stdout + proc.stderr
        self.assertIn("./pfy attach opencode", blob)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["reason"], "no-opencode")
        self.assertFalse(self.marker.exists())
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_ollama_down_is_no_model_and_recovers(self):
        proc, receipt = self.run_build("fix", extra=["--endpoint", "http://127.0.0.1:9/v1"])
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["reason"], "no-model")
        self.assertFalse(self.marker.exists())
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_second_run_blocks_and_the_first_still_passes(self):
        cmd, receipt = self.command("slow-fix", extra=["--timeout", "30"])
        first = subprocess.Popen(
            cmd,
            cwd=self.repo,
            env=self.env("slow-fix", PFY_STUB_SLEEP="2"),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not self.marker.exists():
            if first.poll() is not None:
                break
            time.sleep(0.05)
        self.assertTrue(self.marker.exists(), "first run did not start")
        other_marker = self.tmp / "marker-second"
        proc2, receipt2 = self.run_build(
            "fix",
            env_extra={"PFY_STUB_MARKER": str(other_marker)},
            timeout=15,
        )
        self.assertEqual(proc2.returncode, 4, proc2.stdout + proc2.stderr)
        data2 = self.receipt(proc2, receipt2)
        self.assertEqual(data2["reason"], "another run")
        self.assertFalse(other_marker.exists())
        out, err = first.communicate(timeout=30)
        self.assertEqual(first.returncode, 0, (out or "") + (err or ""))
        data = self.receipt(subprocess.CompletedProcess(cmd, first.returncode, out, err), receipt)
        self.assertEqual(data["status"], "PASS")

    def test_stale_lock_from_a_dead_pid_does_not_block(self):
        lock = self.repo / "tmp" / "local-build.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("42424242\n", encoding="utf-8")
        self.assertTrue(_dead(42424242))
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_model_already_loaded_is_not_unloaded(self):
        self.httpd.ps = [{"name": "fixture:small"}]
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertTrue(data["model_was_loaded"])
        self.assertFalse(data["unloaded"])
        self.assertEqual(_unloads(self.httpd), 0)

    def test_crash_after_the_agent_still_unloads(self):
        proc, receipt = self.run_build("fix", env_extra={"PFY_LOCAL_BUILD_INJECT_CRASH": "post"})
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = self.assert_no_commit(proc, receipt)
        self.assertEqual(data["reason"], "runner-crash")
        self.assertEqual(_unloads(self.httpd), 1)

    def test_timeout_unloads_when_this_run_loaded_the_model(self):
        proc, receipt = self.run_build("hang", extra=["--timeout", "2"], timeout=20)
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(_unloads(self.httpd), 1)
        data = self.receipt(proc, receipt)
        self.assertTrue(data["unloaded"])

    def test_child_env_stays_inside_repo_tmp_and_has_no_secrets(self):
        proc, receipt = self.run_build("fix")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        real_home = Path.home().resolve()
        home = Path(report["home"]).resolve()
        tmpdir = Path(report["tmpdir"]).resolve()
        # The repo itself lives under the user home, so "not the real HOME"
        # means the child HOME is not that directory. Ancestors are expected.
        self.assertNotEqual(home, real_home)
        self.assertTrue(home.parent.name.endswith(".home"), str(home))
        self.assertNotEqual(home, self.repo.resolve())
        # HOME must not be an ancestor of the checkout. The repo lives under
        # the user home on this machine, so the user home is an ancestor of
        # the isolated directory and that is expected.
        self.assertNotIn(home, self.repo.resolve().parents)
        for label, path in (("home", home), ("tmpdir", tmpdir)):
            self.assertTrue(_under_repo_tmp(path, self.repo), label)
            self.assertFalse(_is_system_tmp(path), label)
        isolated = home.parent
        for value in report["xdg"].values():
            path = Path(value).resolve()
            self.assertTrue(_under_repo_tmp(path, self.repo))
            self.assertFalse(_is_system_tmp(path))
            self.assertTrue(path == isolated or isolated in path.parents, str(path))
        for key in report["keys"]:
            upper = key.upper()
            self.assertNotIn("TOKEN", upper, key)
            self.assertNotIn("KEY", upper, key)
            self.assertNotIn("SECRET", upper, key)
        cwd = Path(report["cwd"])
        self.assertTrue(_under_repo_tmp(cwd, self.repo))
        self.assertNotEqual(cwd.resolve(), self.repo.resolve())
        data = self.receipt(proc, receipt)
        self.assertNotIn("ghp_", json.dumps(data))
        self.assertNotIn("AKIA", json.dumps(data))

    def test_dry_run_loads_nothing_and_starts_nothing(self):
        proc, receipt = self.run_build("fix", extra=["--dry-run"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(self.marker.exists())
        self.assertEqual(_unloads(self.httpd), 0)
        for path, payload in self.httpd.posts:
            self.assertNotIn("generate", path)
            self.assertNotIn("chat", path)
            if isinstance(payload, dict):
                self.assertNotIn("keep_alive", payload)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["reason"], "dry-run")
        self.assertIsNone(data["worktree"])
        self.assertEqual(_branches(self.repo), [])

    def test_env_model_is_used_when_the_flag_is_absent(self):
        cmd, receipt = self.command("fix")
        # Drop the flag so the env value has to win over the default tag.
        cleaned = []
        skip = False
        for part in cmd:
            if skip:
                skip = False
                continue
            if part == "--model":
                skip = True
                continue
            cleaned.append(part)
        proc = subprocess.run(
            cleaned,
            cwd=self.repo,
            env=self.env("fix", PFY_LOCAL_BUILD_MODEL="fixture:small"),
            text=True,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = self.receipt(proc, receipt)
        self.assertEqual(data["model"], "fixture:small")


class CloudBuildUnchangedTests(unittest.TestCase):
    def test_help_and_dry_run_stay_the_same(self):
        env = os.environ.copy()
        env["TMPDIR"] = str(ROOT / "tmp" / "scratch")
        help_proc = subprocess.run(
            [str(ROOT / "pfy"), "build", "--help"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(help_proc.returncode, 0, help_proc.stderr)
        self.assertEqual(help_proc.stdout, HELP_GOLDEN)
        dry = subprocess.run(
            [str(ROOT / "pfy"), "build", "-p", "x", "--dry-run"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=60,
        )
        self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
        self.assertEqual(_norm_dry(dry.stdout), DRY_GOLDEN)
        for line in dry.stdout.splitlines():
            if line.startswith("receipt: "):
                path = Path(line.split("receipt: ", 1)[1].strip())
                stamp = path.parent
                if stamp.is_dir() and "pipelines/dogfood/build/" in str(stamp):
                    shutil.rmtree(stamp, ignore_errors=True)

    def test_real_opencode_accepts_the_flags_we_pass(self):
        binary = shutil.which("opencode")
        if not binary:
            self.skipTest("SKIP: opencode-missing")
        version = subprocess.run([binary, "--version"], text=True, capture_output=True, timeout=20)
        self.assertEqual(version.returncode, 0)
        self.assertTrue((version.stdout or version.stderr).strip())
        help_proc = subprocess.run([binary, "run", "--help"], text=True, capture_output=True, timeout=20)
        text = (help_proc.stdout or "") + (help_proc.stderr or "")
        self.assertIn("--pure", text)
        self.assertIn("--model", text)
        self.assertIn("--variant", text)


if __name__ == "__main__":
    unittest.main()
