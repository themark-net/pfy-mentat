#!/usr/bin/env python3
"""pfy build --local: one headless local-model task to a tested branch.

The checkout this process was started from is never switched, reset, stashed,
or committed. Work happens in a detached git worktree under ``<repo>/tmp/``.
Nothing is pushed and no PR is opened.

Exit codes:
  0  PASS, or a clean --dry-run
  1  FAIL (no-change, tests, protected path, interrupt, mem-edge, runner-crash)
  2  usage, or opencode / the model is missing
  3  TIMEOUT (agent)
  4  BLOCKED by a guard (memory, busy host, model size, cloud tag, lock)

Receipt schema: pfy-local-build/1
"""

from __future__ import annotations

import argparse
import fcntl
import fnmatch
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfylib.bot_interface import _scrub, _which_opencode, opencode_config  # noqa: E402

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_TIMEOUT = 3
EXIT_BLOCKED = 4

SCHEMA = "pfy-local-build/1"
DEFAULT_MODEL = "qwen3.6:35b"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/v1"
DEFAULT_TEST_CMD = "python3 -m unittest discover -s tests -t ."
DEFAULT_TIMEOUT = 1200
DEFAULT_TEST_TIMEOUT = 600
DEFAULT_MIN_FREE_GB = 32.0
# examples/local-bench/bench.py DEFAULT_MIN_MEM_GB (Entry 091). Watchdog only.
MEM_EDGE_GIB = 16.0
MAX_MODEL_BYTES = 30 * 1024 * 1024 * 1024
AUTHOR_NAME = "pfy-local-build"
AUTHOR_EMAIL = "pfy-local-build@localhost"
WATCH_SECONDS = 10.0
KILL_GRACE_SECONDS = 5.0

_SECRET_EQ = re.compile(
    r"(?i)\b([A-Za-z0-9_]*(?:TOKEN|KEY|SECRET|PASSWORD)[A-Za-z0-9_]*)\s*=\s*(\S+)"
)
_BEARER = re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._\-]{8,})")
_SK = re.compile(r"\b((?:sk|ghp)_[A-Za-z0-9]{8,})\b")


class UsageError(Exception):
    pass


class State:
    def __init__(self) -> None:
        self.interrupted = False
        self.mem_edge = False
        self.proc: subprocess.Popen | None = None
        self.min_avail: float | None = None
        self.lock_fd = None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _mask(val: str) -> str:
    val = val.strip().strip('"').strip("'")
    if len(val) <= 4:
        return "***"
    return val[:4] + "***"


def redact(text: str) -> str:
    if not text:
        return ""

    def _eq(match: re.Match) -> str:
        return match.group(1) + "=" + _mask(match.group(2))

    text = _SECRET_EQ.sub(_eq, text)
    text = _BEARER.sub(lambda m: m.group(1) + _mask(m.group(2)), text)
    text = _SK.sub(lambda m: _mask(m.group(1)), text)
    return text


def _kb(info: dict, key: str) -> float:
    raw = info.get(key) or ""
    if not raw:
        return 0.0
    try:
        return float(str(raw).split()[0])
    except (TypeError, ValueError, IndexError):
        return 0.0


def read_meminfo() -> dict:
    path = Path(os.environ.get("PFY_MEMINFO_FILE") or "/proc/meminfo")
    out: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for line in lines:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        out[key.strip()] = val.strip()
    return out


def gib(kb: float) -> float:
    return kb / (1024.0 * 1024.0)


def free_ram_plus_swap_gib(info: dict) -> float:
    """MemAvailable + SwapFree. SwapTotal is capacity, not free headroom."""
    return gib(_kb(info, "MemAvailable") + _kb(info, "SwapFree"))


def mem_available_gib(info: dict) -> float:
    return gib(_kb(info, "MemAvailable"))


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _http_json(method: str, url: str, body=None, timeout: float = 5):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json", "User-Agent": "pfy-local-build/1"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
        return resp.status, json.loads(raw) if raw else {}


def _slug(text: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return (raw[:40] or "task").strip("-") or "task"


def _endpoint_pair(raw: str) -> tuple[str, str]:
    ep = (raw or "").strip().rstrip("/") or DEFAULT_ENDPOINT
    if ep.endswith("/v1"):
        return ep[: -len("/v1")], ep
    return ep, ep + "/v1"


def _host_only(openai_base: str) -> str:
    root, _base = _endpoint_pair(openai_base)
    no_scheme = root.split("://", 1)[-1]
    return no_scheme.split("/", 1)[0]


def _is_cloud_tag(name: str) -> bool:
    return ":cloud" in (name or "").lower()


def _same_model(left: str, right: str) -> bool:
    def norm(name: str) -> str:
        name = (name or "").strip()
        if name.endswith(":latest"):
            name = name[: -len(":latest")]
        return name

    return norm(left) == norm(right)


def _pick_str(flag: str | None, env_name: str, default: str) -> str:
    if flag is not None and str(flag).strip() != "":
        return str(flag).strip()
    raw = os.environ.get(env_name)
    if raw is not None and raw.strip() != "":
        return raw.strip()
    return default


def _pick_float(flag: float | None, env_name: str, default: float) -> float:
    if flag is not None:
        return float(flag)
    raw = os.environ.get(env_name)
    if raw is not None and raw.strip() != "":
        return float(raw.strip())
    return default


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pfy build --local",
        description="Headless local-model build. One task, one tested branch, no push.",
    )
    parser.add_argument("task", nargs="?", help="task text")
    parser.add_argument("--local", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--repo", default=None, help="git repo (default: repo that contains the cwd)")
    parser.add_argument("--base", default=None, help="base ref (default: origin/main, else HEAD)")
    parser.add_argument("--model", default=None, help="Ollama tag (env PFY_LOCAL_BUILD_MODEL)")
    parser.add_argument("--endpoint", default=None, help="OpenAI base URL (env LOCAL_OPENAI_BASE_URL)")
    parser.add_argument("--test-cmd", default=None, help="gate command (env PFY_LOCAL_BUILD_TEST_CMD)")
    parser.add_argument("--timeout", type=float, default=None, help="agent seconds (env PFY_LOCAL_BUILD_TIMEOUT)")
    parser.add_argument("--test-timeout", type=float, default=None, help="test command seconds")
    parser.add_argument("--min-free-gb", type=float, default=None, help="MemAvailable+SwapFree floor")
    parser.add_argument("--protect", action="append", default=[], help="glob the agent must not change")
    parser.add_argument("--prompt-file", default=None, help="read the task from this file")
    parser.add_argument("--receipt-dir", default=None, help="directory for receipt.json")
    parser.add_argument("--keep-worktree", action="store_true", help="keep the worktree after PASS")
    parser.add_argument("--dry-run", action="store_true", help="pre-flight only: start nothing, load nothing")
    parser.add_argument("--run-tests-on-timeout", action="store_true", help="run the gate after TIMEOUT")
    parser.add_argument("--keep-model", action="store_true", help="do not unload at the end")
    parser.add_argument(
        "--unload-at-end",
        action="store_true",
        help="unload the requested model at the end if the agent started",
    )
    args = parser.parse_args(argv)
    if args.task and args.prompt_file:
        raise UsageError("PASS one task string or --prompt-file, not both")
    task = args.task
    if args.prompt_file:
        path = Path(args.prompt_file)
        if not path.is_file():
            raise UsageError("prompt file not found: %s" % path)
        task = path.read_text(encoding="utf-8")
    if not task or not str(task).strip():
        raise UsageError("a task string or --prompt-file is required")
    args.task_text = str(task)
    try:
        args.model_name = _pick_str(args.model, "PFY_LOCAL_BUILD_MODEL", DEFAULT_MODEL)
        args.endpoint_raw = _pick_str(args.endpoint, "LOCAL_OPENAI_BASE_URL", DEFAULT_ENDPOINT)
        args.test_cmd_s = _pick_str(args.test_cmd, "PFY_LOCAL_BUILD_TEST_CMD", DEFAULT_TEST_CMD)
        args.timeout_s = _pick_float(args.timeout, "PFY_LOCAL_BUILD_TIMEOUT", DEFAULT_TIMEOUT)
        args.test_timeout_s = _pick_float(args.test_timeout, "PFY_LOCAL_BUILD_TEST_TIMEOUT", DEFAULT_TEST_TIMEOUT)
        args.min_free = _pick_float(args.min_free_gb, "PFY_LOCAL_BUILD_MIN_FREE_GB", DEFAULT_MIN_FREE_GB)
    except ValueError as exc:
        raise UsageError("a numeric flag or env value is not a number") from exc
    if args.timeout_s <= 0 or args.test_timeout_s <= 0 or args.min_free < 0:
        raise UsageError("timeout and min-free-gb must be positive (min-free-gb may be 0)")
    return args


def _git(repo: Path, args: list[str], env: dict | None = None, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def resolve_repo(raw: str | None) -> Path:
    start = Path(raw).resolve() if raw else Path.cwd()
    if not start.exists():
        raise UsageError("repo path does not exist: %s" % start)
    proc = _git(start if start.is_dir() else start.parent, ["rev-parse", "--show-toplevel"])
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        raise UsageError("not a git repo: %s" % start)
    return Path(proc.stdout.strip()).resolve()


def resolve_base(repo: Path, requested: str | None) -> str:
    if requested and requested.strip():
        ref = requested.strip()
    else:
        probe = _git(repo, ["rev-parse", "--verify", "--quiet", "origin/main"])
        ref = "origin/main" if probe.returncode == 0 else "HEAD"
    sha = _git(repo, ["rev-parse", ref])
    if sha.returncode != 0 or not (sha.stdout or "").strip():
        raise UsageError("base ref not found: %s" % ref)
    return ref


def _child_env(extra: dict[str, str]) -> dict[str, str]:
    forwarded = {}
    for key, val in os.environ.items():
        if key == "PFY_LOCAL_BUILD_SCENARIO" or key.startswith("PFY_STUB_"):
            forwarded[key] = val
    forwarded.update(extra)
    return _scrub(os.environ, **forwarded)


def _signal_group(proc: subprocess.Popen, sig: int) -> bool:
    if proc.poll() is not None:
        return True
    try:
        os.killpg(proc.pid, sig)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(proc.pid, sig)
        except OSError:
            return False
        return False


def _kill_group(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    _signal_group(proc, signal.SIGTERM)
    deadline = time.monotonic() + KILL_GRACE_SECONDS
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.05)
    _signal_group(proc, signal.SIGKILL)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def _drain(proc: subprocess.Popen, box: dict) -> None:
    try:
        out, err = proc.communicate()
    except Exception as exc:  # noqa: BLE001
        box["error"] = str(exc)
        out, err = "", ""
    box["out"] = out or ""
    box["err"] = err or ""
    box["code"] = proc.returncode


def run_bounded(cmd: list[str], env: dict, cwd: Path, timeout: float, state: State) -> tuple[str, int | None, str, str]:
    """Run cmd in its own session. Returns (status, code, stdout, stderr).

    status is done, timeout, interrupted, or mem-edge.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    state.proc = proc
    box: dict = {}
    reader = threading.Thread(target=_drain, args=(proc, box), daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    status = "done"
    while reader.is_alive():
        if state.interrupted:
            status = "interrupted"
            _kill_group(proc)
            break
        if state.mem_edge:
            status = "mem-edge"
            _kill_group(proc)
            break
        if time.monotonic() >= deadline:
            status = "timeout"
            _kill_group(proc)
            break
        time.sleep(0.05)
    reader.join(timeout=10)
    state.proc = None
    return status, box.get("code"), box.get("out") or "", box.get("err") or ""


def _tail(text: str, lines: int = 40) -> str:
    parts = (text or "").splitlines()
    return "\n".join(parts[-lines:])


def parse_unittest_counts(text: str) -> dict | None:
    match = re.search(r"^Ran (\d+) tests?\b", text or "", re.M)
    if not match:
        return None
    ran = int(match.group(1))
    failed_m = re.search(r"failures=(\d+)", text)
    errors_m = re.search(r"errors=(\d+)", text)
    skipped_m = re.search(r"skipped=(\d+)", text)
    failed = int(failed_m.group(1)) if failed_m else 0
    errors = int(errors_m.group(1)) if errors_m else 0
    skipped = int(skipped_m.group(1)) if skipped_m else 0
    passed = max(0, ran - failed - errors - skipped)
    sec_m = re.search(r"Ran \d+ tests? in ([0-9.]+)s", text)
    seconds = float(sec_m.group(1)) if sec_m else None
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "ran": ran,
        "seconds": seconds,
    }


def _total(counts: dict | None) -> int | None:
    if not counts:
        return None
    return int(counts["ran"])


def judge_tests(before: dict, after: dict) -> str | None:
    """None means the gate passed. Otherwise a FAIL reason."""
    if not after.get("started"):
        return "test-cmd-failed-to-start"
    if after.get("exit") != 0:
        return "tests-failed"
    after_counts = after.get("counts")
    before_counts = before.get("counts")
    if after_counts is not None and before_counts is not None:
        if _total(after_counts) < _total(before_counts):
            return "tests-regressed"
        if after_counts["failed"] > before_counts["failed"] or after_counts["errors"] > before_counts["errors"]:
            return "tests-failed"
        return None
    before_total = _total(before_counts) or 0
    before_bad = before.get("exit") not in (0, None)
    if before_bad or before_total >= 1:
        return None
    return "tests-failed"


def _test_record(cmd: str, started: bool, exit_code: int | None, text: str, seconds: float) -> dict:
    counts = parse_unittest_counts(text) if started else None
    return {
        "cmd": cmd,
        "exit": exit_code,
        "passed": None if not counts else counts["passed"],
        "failed": None if not counts else counts["failed"],
        "errors": None if not counts else counts["errors"],
        "seconds": round(seconds, 3),
        "tail": redact(_tail(text)),
        "started": started,
        "counts": counts,
    }


def run_tests(cmd_s: str, cwd: Path, env: dict, timeout: float, state: State) -> dict:
    argv = shlex.split(cmd_s)
    if not argv:
        return _test_record(cmd_s, False, None, "empty test command", 0.0)
    started = time.monotonic()
    try:
        status, code, out, err = run_bounded(argv, env, cwd, timeout, state)
    except FileNotFoundError:
        return _test_record(cmd_s, False, None, "command not found", 0.0)
    except OSError as exc:
        if getattr(exc, "errno", None) == 2:
            return _test_record(cmd_s, False, None, "command not found", 0.0)
        return _test_record(cmd_s, False, None, str(exc), 0.0)
    elapsed = time.monotonic() - started
    text = (out or "") + ("\n" + err if err else "")
    if status == "timeout":
        rec = _test_record(cmd_s, True, code if code is not None else 124, text + "\ntest-timeout", elapsed)
        rec["exit"] = 124
        return rec
    if status in ("interrupted", "mem-edge"):
        rec = _test_record(cmd_s, True, code, text, elapsed)
        rec["aborted"] = status
        return rec
    # File-not-found from a missing executable is an OSError before Popen returns
    # in normal cases. A shell-less missing argv[0] raises FileNotFoundError.
    return _test_record(cmd_s, True, code if code is not None else 1, text, elapsed)


def _protected(path: str, patterns: list[str]) -> bool:
    rel = path.replace("\\", "/").lstrip("./")
    for pattern in patterns:
        pat = pattern.replace("\\", "/").strip()
        if not pat:
            continue
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(Path(rel).name, pat):
            return True
        if pat.endswith("/**"):
            prefix = pat[:-3].rstrip("/")
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
    return False


def files_changed(worktree: Path, env: dict) -> list[str]:
    proc = _git(worktree, ["status", "--porcelain", "-uall"], env=env)
    found = []
    for line in (proc.stdout or "").splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        path = path.replace("\\", "/")
        if path == "tmp" or path.startswith("tmp/"):
            continue
        if path.startswith("__pycache__/") or path.endswith(".pyc") or "/__pycache__/" in path:
            continue
        found.append(path)
    return found


def _ensure_tmp_excluded(worktree: Path, env: dict) -> None:
    (worktree / "tmp").mkdir(parents=True, exist_ok=True)
    raw = _git(worktree, ["rev-parse", "--git-path", "info/exclude"], env=env)
    if raw.returncode != 0:
        return
    path = Path((raw.stdout or "").strip())
    if not path.is_absolute():
        path = (worktree / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = [ln.strip() for ln in text.splitlines()]
    extra = ["tmp/", "__pycache__/", "*.pyc"]
    missing = [item for item in extra if item not in lines]
    if not missing:
        return
    with path.open("a", encoding="utf-8") as handle:
        if text and not text.endswith("\n"):
            handle.write("\n")
        for item in missing:
            handle.write(item + "\n")


def _acquire_lock(path: Path) -> object | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = open(path, "a+", encoding="utf-8")
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.seek(0)
        raw = fd.read().strip()
        fd.close()
        pid = int(raw) if raw.isdigit() else None
        if pid and not _alive(pid):
            fd = open(path, "a+", encoding="utf-8")
            try:
                fcntl.flock(fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fd.close()
                return None
        else:
            return None
    fd.seek(0)
    fd.truncate()
    fd.write(str(os.getpid()))
    fd.flush()
    return fd


def _release_lock(fd) -> None:
    if fd is None:
        return
    try:
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        fd.close()
    except OSError:
        pass


def _ollama_tags(root: str) -> tuple[list[dict] | None, str | None]:
    try:
        status, data = _http_json("GET", root.rstrip("/") + "/api/tags", timeout=3)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return None, "unreachable"
    if status != 200 or not isinstance(data, dict):
        return None, "unreachable"
    models = data.get("models")
    if not isinstance(models, list):
        return [], None
    return models, None


def _tag_of(model: str, tags: list[dict]) -> dict | None:
    for item in tags:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model") or ""
        if _same_model(str(name), model):
            return item
    return None


def _ps_names(root: str) -> list[str] | None:
    try:
        status, data = _http_json("GET", root.rstrip("/") + "/api/ps", timeout=3)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        status, data = 0, None
    if status == 200 and isinstance(data, dict):
        names = []
        for item in data.get("models") or []:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name") or item.get("model") or ""
                if str(name).strip():
                    names.append(str(name).strip())
        return names
    try:
        proc = subprocess.run(
            ["ollama", "ps"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or "").strip()
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    names = []
    for ln in lines[1:]:
        parts = re.split(r"\s{2,}", ln.strip())
        if parts and parts[0] and parts[0].lower() != "name":
            names.append(parts[0])
    return names


def _model_size(tag: dict) -> int | None:
    raw = tag.get("size")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def unload_model(root: str, model: str) -> bool:
    body = {
        "model": model,
        "prompt": "",
        "stream": False,
        "keep_alive": 0,
        "options": {"num_ctx": 512, "num_predict": 1},
    }
    try:
        status, _data = _http_json("POST", root.rstrip("/") + "/api/generate", body, timeout=30)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return False
    return status == 200


def _write_config(home: Path, base: str, model: str) -> Path:
    cfg = opencode_config(base, model)
    cfg["permission"] = {
        "read": "allow",
        "edit": "allow",
        "bash": {
            "*": "allow",
            # Last match wins. A slash after a space or a redirect, or "..",
            # is a path outside this worktree or an absolute path. In-tree
            # commands such as `python3 -m unittest discover -s tests -t .`
            # do not match these. opencode 1.18 does not treat a shell
            # redirect as external_directory, so the pattern is the backstop.
            "* /*": "deny",
            "*>/*": "deny",
            "*..*": "deny",
            "git commit*": "deny",
            "git push*": "deny",
            "git reset*": "deny",
            "git checkout*": "deny",
            "git switch*": "deny",
            "git clean*": "deny",
        },
        "external_directory": "deny",
        "webfetch": "deny",
        "websearch": "deny",
        "question": "deny",
    }
    path = home / "config" / "opencode" / "opencode.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path


def _agent_prompt(task: str, test_cmd: str) -> str:
    return (
        "Work only in this directory. Edit files. Run the tests yourself. "
        "Do not commit. Do not touch anything outside this directory.\n\n"
        "Test command: %s\n\n"
        "Task:\n%s" % (test_cmd, task)
    )


def _opencode_env(home: Path, worktree: Path, base: str, config: Path) -> dict[str, str]:
    return _child_env(
        {
            "OPENAI_BASE_URL": base,
            "HOME": str(home / "home"),
            "XDG_CONFIG_HOME": str(home / "config"),
            "XDG_DATA_HOME": str(home / "data"),
            "XDG_CACHE_HOME": str(home / "cache"),
            "XDG_STATE_HOME": str(home / "state"),
            "OPENCODE_CONFIG": str(config),
            "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
            "OPENCODE_DISABLE_MODELS_FETCH": "1",
            "OPENCODE_DISABLE_SHARE": "1",
            "OPENCODE_DISABLE_CLAUDE_CODE": "1",
            "OPENCODE_DISABLE_EXTERNAL_SKILLS": "1",
            "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
            "TMPDIR": str(worktree / "tmp"),
        }
    )


def _prepare_home(home: Path) -> None:
    for name in ("home", "config", "data", "cache", "state"):
        (home / name).mkdir(parents=True, exist_ok=True)


def _public_test(rec: dict | None) -> dict | None:
    if rec is None:
        return None
    return {
        "cmd": rec.get("cmd"),
        "exit": rec.get("exit"),
        "passed": rec.get("passed"),
        "failed": rec.get("failed"),
        "errors": rec.get("errors"),
        "seconds": rec.get("seconds"),
        "tail": rec.get("tail"),
    }


def _write_receipt(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _summary(status: str, reason: str, branch: str | None, receipt: Path) -> str:
    label = status
    if status == "BLOCKED":
        label = "BLOCKED:"
    shown = reason or ""
    return "%s %s branch=%s receipt=%s" % (label, shown, branch or "none", receipt)


def _install_signals(state: State) -> None:
    def _handle(signum, _frame):
        state.interrupted = True
        proc = state.proc
        if proc is not None and proc.poll() is None:
            _signal_group(proc, signal.SIGTERM)

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)


def _watchdog(stop: threading.Event, state: State) -> None:
    while not stop.wait(WATCH_SECONDS):
        avail = mem_available_gib(read_meminfo())
        if state.min_avail is None:
            state.min_avail = avail
        else:
            state.min_avail = min(state.min_avail, avail)
        if avail < MEM_EDGE_GIB:
            state.mem_edge = True
            proc = state.proc
            if proc is not None and proc.poll() is None:
                _signal_group(proc, signal.SIGTERM)
            return


def _git_env(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    return env


def build_local(argv: list[str] | None = None) -> int:
    state = State()
    _install_signals(state)
    try:
        args = parse_args(argv)
    except UsageError as exc:
        print("FAIL: %s" % exc, file=sys.stderr)
        return EXIT_USAGE

    started = time.monotonic()
    started_at = _now()
    stamp = _stamp()
    slug = _slug(args.task_text)
    receipt_path: Path | None = None
    home: Path | None = None
    worktree: Path | None = None
    branch: str | None = None
    commit: str | None = None
    status = "FAIL"
    reason = "runner-crash"
    exit_code = EXIT_FAIL
    tests_before = None
    tests_after = None
    changed: list[str] = []
    agent_log: Path | None = None
    agent_seconds = 0.0
    model_was_loaded = False
    unloaded = False
    agent_started = False
    opencode_version = None
    base_ref = None
    base_sha = None
    repo = None
    ollama_root = None
    mem_start = read_meminfo()
    state.min_avail = mem_available_gib(mem_start)
    stop_watch = threading.Event()
    watcher = None

    def finish() -> int:
        nonlocal unloaded
        finished_at = _now()
        if receipt_path is not None:
            payload = {
                "schema": SCHEMA,
                "id": stamp + "-" + slug,
                "task": redact(args.task_text)[:500],
                "repo": None if repo is None else str(repo),
                "base_sha": base_sha,
                "model": args.model_name,
                "endpoint": _host_only(args.endpoint_raw),
                "status": status,
                "reason": reason,
                "exit_code": exit_code,
                "wall_seconds": round(time.monotonic() - started, 3),
                "agent_seconds": round(agent_seconds, 3),
                "tests_before": _public_test(tests_before),
                "tests_after": _public_test(tests_after),
                "files_changed": changed,
                "branch": branch,
                "commit": commit,
                "worktree": None if worktree is None else str(worktree),
                "model_was_loaded": model_was_loaded,
                "unloaded": unloaded,
                "mem": {
                    "mem_available_gb": round(mem_available_gib(mem_start), 3),
                    "swap_free_gb": round(gib(_kb(mem_start, "SwapFree")), 3),
                    "min_available_gb": None if state.min_avail is None else round(state.min_avail, 3),
                },
                "opencode_version": opencode_version,
                "agent_log": None if agent_log is None else str(agent_log),
                "started_at": started_at,
                "finished_at": finished_at,
            }
            _write_receipt(receipt_path, payload)
            print(_summary(status, reason, branch, receipt_path))
        stop_watch.set()
        if watcher is not None:
            watcher.join(timeout=1)
        if ollama_root and _should_unload():
            unloaded = unload_model(ollama_root, args.model_name)
            if receipt_path is not None and receipt_path.is_file():
                try:
                    current = json.loads(receipt_path.read_text(encoding="utf-8"))
                    current["unloaded"] = unloaded
                    _write_receipt(receipt_path, current)
                except (OSError, json.JSONDecodeError):
                    pass
        _release_lock(state.lock_fd)
        state.lock_fd = None
        return exit_code

    def _should_unload() -> bool:
        if not agent_started:
            return False
        if args.unload_at_end:
            return True
        if args.keep_model:
            return False
        return not model_was_loaded

    try:
        repo = resolve_repo(args.repo)
        base_ref = resolve_base(repo, args.base)
        sha_proc = _git(repo, ["rev-parse", base_ref])
        base_sha = (sha_proc.stdout or "").strip() or None
        ollama_root, openai_base = _endpoint_pair(args.endpoint_raw)
        if args.receipt_dir:
            receipt_dir = Path(args.receipt_dir).resolve()
        else:
            receipt_dir = repo / "pipelines" / "dogfood" / "build-local" / stamp
        receipt_path = receipt_dir / "receipt.json"
        receipt_dir.mkdir(parents=True, exist_ok=True)

        lock_path = repo / "tmp" / "local-build.lock"
        state.lock_fd = _acquire_lock(lock_path)
        if state.lock_fd is None:
            status, reason, exit_code = "BLOCKED", "another run", EXIT_BLOCKED
            return finish()

        if state.interrupted:
            status, reason, exit_code = "FAIL", "interrupted", EXIT_FAIL
            return finish()

        free = free_ram_plus_swap_gib(mem_start)
        if free < args.min_free:
            status, reason, exit_code = "BLOCKED", "mem", EXIT_BLOCKED
            return finish()

        binary = _which_opencode(os.environ)
        if not binary:
            print("BLOCKED: no-opencode", file=sys.stderr)
            print("  next: ./pfy attach opencode", file=sys.stderr)
            status, reason, exit_code = "BLOCKED", "no-opencode", EXIT_USAGE
            return finish()

        if _is_cloud_tag(args.model_name):
            status, reason, exit_code = "BLOCKED", "cloud-tag", EXIT_BLOCKED
            return finish()

        tags, tag_err = _ollama_tags(ollama_root)
        if tag_err or tags is None:
            status, reason, exit_code = "BLOCKED", "no-model", EXIT_USAGE
            return finish()
        tag = _tag_of(args.model_name, tags)
        if tag is None:
            status, reason, exit_code = "BLOCKED", "no-model", EXIT_USAGE
            return finish()
        size = _model_size(tag)
        if size is not None and size > MAX_MODEL_BYTES:
            status, reason, exit_code = "BLOCKED", "model-too-big", EXIT_BLOCKED
            return finish()

        loaded = _ps_names(ollama_root)
        if loaded is None:
            loaded = []
        others = [name for name in loaded if not _same_model(name, args.model_name)]
        if others:
            status, reason, exit_code = "BLOCKED", "busy-host", EXIT_BLOCKED
            return finish()
        model_was_loaded = any(_same_model(name, args.model_name) for name in loaded)

        if args.dry_run:
            print("dry-run: repo=%s" % repo)
            print("dry-run: base=%s sha=%s" % (base_ref, base_sha))
            print("dry-run: model=%s endpoint=%s" % (args.model_name, _host_only(args.endpoint_raw)))
            print("dry-run: test_cmd=%s" % args.test_cmd_s)
            print("dry-run: min_free_gb=%s free_gib=%.3f" % (args.min_free, free))
            print("dry-run: worktree would be %s" % (repo / "tmp" / ("local-build-%s-%s" % (stamp, slug))))
            print("dry-run: start nothing, load nothing")
            status, reason, exit_code = "PASS", "dry-run", EXIT_OK
            return finish()

        (repo / "tmp").mkdir(parents=True, exist_ok=True)
        (receipt_dir / "version-home").mkdir(parents=True, exist_ok=True)
        ver = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            stdin=subprocess.DEVNULL,
            env=_scrub(os.environ, HOME=str(receipt_dir / "version-home"), TMPDIR=str(repo / "tmp")),
        )
        opencode_version = redact(((ver.stdout or "") + (ver.stderr or "")).strip().splitlines()[0] if (ver.stdout or ver.stderr) else "") or None

        wt_path = repo / "tmp" / ("local-build-%s-%s" % (stamp, slug))
        home = repo / "tmp" / ("local-build-%s-%s.home" % (stamp, slug))
        if wt_path.exists() or home.exists():
            status, reason, exit_code = "FAIL", "worktree-exists", EXIT_FAIL
            return finish()
        (repo / "tmp").mkdir(parents=True, exist_ok=True)
        added = _git(repo, ["worktree", "add", "--detach", str(wt_path), base_ref])
        if added.returncode != 0:
            status, reason, exit_code = "FAIL", "worktree-failed", EXIT_FAIL
            return finish()
        worktree = wt_path
        _ensure_tmp_excluded(worktree, _child_env({"TMPDIR": str(worktree / "tmp")}))
        (worktree / "tmp").mkdir(parents=True, exist_ok=True)

        test_env = _child_env(
            {
                "TMPDIR": str(worktree / "tmp"),
                "HOME": str(home / "home"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        home.mkdir(parents=True, exist_ok=True)
        _prepare_home(home)

        watcher = threading.Thread(target=_watchdog, args=(stop_watch, state), daemon=True)
        watcher.start()

        tests_before = run_tests(args.test_cmd_s, worktree, test_env, args.test_timeout_s, state)
        if tests_before.get("aborted") == "interrupted" or state.interrupted:
            status, reason, exit_code = "FAIL", "interrupted", EXIT_FAIL
            return finish()
        if tests_before.get("aborted") == "mem-edge" or state.mem_edge:
            status, reason, exit_code = "FAIL", "mem-edge", EXIT_FAIL
            return finish()
        if not tests_before.get("started"):
            status, reason, exit_code = "FAIL", "test-cmd-failed-to-start", EXIT_FAIL
            return finish()

        config = _write_config(home, openai_base, args.model_name)
        child = _opencode_env(home, worktree, openai_base, config)
        prompt = _agent_prompt(args.task_text, args.test_cmd_s)
        cmd = [binary, "run", "--pure", "--model", "ollama/%s" % args.model_name, "--variant", "none", prompt]
        agent_started = True
        agent_t0 = time.monotonic()
        run_status, _code, out, err = run_bounded(cmd, child, worktree, args.timeout_s, state)
        agent_seconds = time.monotonic() - agent_t0
        agent_log = receipt_dir / "agent.log"
        agent_log.write_text(
            "----- stdout -----\n%s\n----- stderr -----\n%s\n" % (redact(out), redact(err)),
            encoding="utf-8",
        )

        if os.environ.get("PFY_LOCAL_BUILD_INJECT_CRASH") == "post" and run_status == "done":
            raise RuntimeError("injected post crash")

        if run_status == "interrupted" or state.interrupted:
            status, reason, exit_code = "FAIL", "interrupted", EXIT_FAIL
            return finish()
        if run_status == "mem-edge" or state.mem_edge:
            status, reason, exit_code = "FAIL", "mem-edge", EXIT_FAIL
            return finish()
        if run_status == "timeout" and not args.run_tests_on_timeout:
            status, reason, exit_code = "TIMEOUT", "timeout", EXIT_TIMEOUT
            return finish()

        changed = files_changed(worktree, test_env)
        if not changed:
            status, reason, exit_code = "FAIL", "no-change", EXIT_FAIL
            return finish()
        protected_hits = [path for path in changed if _protected(path, args.protect or [])]
        if protected_hits:
            status, reason, exit_code = "FAIL", "protected-path-changed", EXIT_FAIL
            return finish()

        tests_after = run_tests(args.test_cmd_s, worktree, test_env, args.test_timeout_s, state)
        if tests_after.get("aborted") == "interrupted" or state.interrupted:
            status, reason, exit_code = "FAIL", "interrupted", EXIT_FAIL
            return finish()
        gate = judge_tests(tests_before, tests_after)
        if gate:
            status, reason, exit_code = "FAIL", gate, EXIT_FAIL
            return finish()
        if run_status == "timeout":
            status, reason, exit_code = "TIMEOUT", "timeout", EXIT_TIMEOUT
            return finish()

        commit_env = _git_env(test_env)
        title = " ".join(args.task_text.split())[:80] or "task"
        message = "%s\n\nreceipt: %s\n" % (title, stamp + "-" + slug)
        committed = _git(worktree, ["add", "-A"], env=commit_env)
        if committed.returncode != 0:
            status, reason, exit_code = "FAIL", "commit-failed", EXIT_FAIL
            return finish()
        committed = _git(worktree, ["commit", "-m", message], env=commit_env)
        if committed.returncode != 0:
            status, reason, exit_code = "FAIL", "commit-failed", EXIT_FAIL
            return finish()
        branch_name = "local/%s-%s" % (slug, stamp)
        made = _git(worktree, ["branch", branch_name, "HEAD"], env=commit_env)
        if made.returncode != 0:
            status, reason, exit_code = "FAIL", "commit-failed", EXIT_FAIL
            return finish()
        _git(worktree, ["switch", branch_name], env=commit_env)
        sha = _git(worktree, ["rev-parse", "HEAD"], env=commit_env)
        branch = branch_name
        commit = (sha.stdout or "").strip() or None
        status, reason, exit_code = "PASS", "ok", EXIT_OK
        if not args.keep_worktree:
            _git(repo, ["worktree", "remove", str(worktree)])
        return finish()
    except UsageError as exc:
        print("FAIL: %s" % exc, file=sys.stderr)
        status, reason, exit_code = "BLOCKED", "usage", EXIT_USAGE
        return finish()
    except Exception:
        status, reason, exit_code = "FAIL", "runner-crash", EXIT_FAIL
        return finish()
    finally:
        stop_watch.set()


def main(argv: list[str] | None = None) -> int:
    return build_local(argv)


if __name__ == "__main__":
    sys.exit(main())
