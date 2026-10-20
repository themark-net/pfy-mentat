#!/usr/bin/env python3
"""Network-limited bwrap sandbox for local Harness².

The host process is the only thing that sees the allow-list. The child runs
in a mount and network namespace. One unix socket under ``$STATE/r`` carries
exposed loopback ports back to the host, and the host forwards a port only
when it is in ``--allow``. Stdin is inherited so ``sbun`` can close it with
``</dev/null``.
"""
from __future__ import annotations

import fcntl
import json
import os
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path

SUN_PATH_MAX = 107
# A llama-server request may stay silent for a long prefill or while it waits
# behind -np 1. The splice idle budget is the per-request client timeout.
# The watchdog, not this cut, is what ends a dead relay.
RELAY_IDLE_S = 600.0
# Spec: a round trip every 10 s, including after a miss. Two misses kill.
WATCHDOG_GAP_S = 10.0
BLOCK_NAMES = (
    "opencode.json",
    "opencode.jsonc",
    "config.json",
    ".opencode",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTEXT.md",
)
OPENCODE_EXACT = {
    "OPENCODE_DISABLE_MODELS_FETCH",
    "OPENCODE_DISABLE_AUTOUPDATE",
    "OPENCODE_DISABLE_LSP_DOWNLOAD",
    "OPENCODE_DISABLE_DEFAULT_PLUGINS",
    "OPENCODE_DISABLE_EXTERNAL_SKILLS",
    "OPENCODE_DISABLE_CLAUDE_CODE",
    "OPENCODE_PERMISSION",
    "OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX",
}
OPENCODE_DROPPED = {
    "OPENCODE_CONFIG",
    "OPENCODE_CONFIG_DIR",
    "OPENCODE_CONFIG_CONTENT",
    "OPENCODE_TEST_MANAGED_CONFIG_DIR",
}
PASS_EXACT = {
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "TZ",
    "TERM",
    "PYTHONUNBUFFERED",
    "PYTHONDONTWRITEBYTECODE",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
}


def die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _acquire_call_lock(host_only: Path) -> int:
    """Exclusive lock for the whole call. The file is never bound into the sandbox."""
    host_only.mkdir(parents=True, exist_ok=True)
    fd = os.open(host_only / "call.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        die("BLOCKED: call in progress")
    return fd


def bun_path() -> Path:
    """Host wrapper. Upstream calls ``config.BUN.is_file()``; this stays a Path."""
    return Path(__file__).resolve().with_name("sbun")


def _worktree() -> Path:
    env = os.environ.get("HARNESS2_W")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[2]


def _unescape_mount(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 3 < len(text) and text[i + 1 : i + 4].isdigit():
            out.append(chr(int(text[i + 1 : i + 4], 8)))
            i += 4
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _parse_mounts(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        rows.append((_unescape_mount(parts[1]), parts[3]))
    return rows


def _second_net(name: str) -> bool:
    """True when an allow-listed name is still a secret and must be dropped."""
    xdir = Path(__file__).resolve().parents[1] / "x-intake-local"
    if str(xdir) not in sys.path:
        sys.path.insert(0, str(xdir))
    import smoke  # noqa: E402

    upper = name.upper()
    if name in smoke.PAID_KEYS or name == "TOKEN":
        return True
    if smoke.SECRET_ENV_RE.search(name):
        return True
    if name.endswith("_KEY") or "CREDENTIALS" in upper or "GITHUB_PAT" in upper:
        return True
    if upper.startswith("GOOGLE_") or "VERTEX" in upper:
        return True
    return False


def _allowed_name(name: str) -> bool:
    if name in OPENCODE_DROPPED:
        return False
    if name in PASS_EXACT or name in OPENCODE_EXACT:
        return True
    if name.startswith("LC_"):
        return True
    if name.startswith("UV_"):
        return True
    if name.startswith("npm_config_"):
        return True
    if name.startswith("BUN_INSTALL"):
        return True
    if name.startswith("HARNESS2_"):
        return True
    return False


def build_env(host: dict[str, str], *, home: str, state: Path, harness: Path) -> dict[str, str]:
    env = {}
    for key, value in host.items():
        if not _allowed_name(key):
            continue
        if _second_net(key):
            continue
        env[key] = value
    venv_bin = harness / ".venv" / "bin"
    tools_bin = harness / "dependencies" / "tools" / "node_modules" / ".bin"
    env["PATH"] = f"{venv_bin}:{tools_bin}:/usr/bin:/bin"
    env["HOME"] = home
    env["XDG_CONFIG_HOME"] = str(Path(home) / ".config")
    env["XDG_CACHE_HOME"] = str(Path(home) / ".cache")
    env["OPENCODE_CONFIG"] = str(state / "opencode.json")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def merged_usr_args() -> list[str]:
    """Refuse a non-merged /usr layout. Add /lib32 only when /usr/lib32 exists."""
    for name in ("/bin", "/sbin", "/lib", "/lib64"):
        if not os.path.islink(name):
            die("not merged-usr")
        target = os.readlink(name)
        if "usr/" not in target and not target.startswith("/usr/"):
            die("not merged-usr")
    argv = [
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/bin", "/bin",
        "--symlink", "usr/sbin", "/sbin",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64",
    ]
    if os.path.isdir("/usr/lib32"):
        argv += ["--symlink", "usr/lib32", "/lib32"]
    return argv


def assert_tools() -> None:
    for name in ("git", "rg"):
        path = Path("/usr/bin") / name
        if not path.is_file() or not os.access(path, os.X_OK):
            die(f"{name} missing")


def resolve_py312(explicit: str | None, home: str) -> Path:
    home_root = str(Path(home) / ".local" / "share" / "uv" / "python")
    if explicit:
        path = Path(explicit).resolve()
        if not str(path).startswith(home_root + os.sep) and str(path) != home_root:
            die(f"python312 not under {home_root}")
        return path
    root = Path(home) / ".local/share/uv/python"
    preferred = root / "cpython-3.12.12-linux-x86_64-gnu/bin/python3.12"
    found: list[Path] = []
    if preferred.is_file():
        found.append(preferred)
    if root.is_dir():
        for cand in sorted(root.glob("cpython-3.12.*/bin/python3.12")):
            if cand.is_file() and cand not in found:
                found.append(cand)
    if not found:
        die("BLOCKED: no-python312")
    candidate = found[0]
    real_bin = Path(os.path.realpath(candidate))
    probe = subprocess.run(
        [str(real_bin), "-c", "import sys; print(sys.base_prefix)"],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        die("BLOCKED: no-python312")
    prefix = Path(os.path.realpath(probe.stdout.strip()))
    if not str(prefix).startswith(home_root + os.sep):
        die(f"python312 not under {home_root}")
    return prefix


def build_bwrap(bwrap: str, *, home: str, harness: Path, runs: Path, ws: Path,
                state: Path, py312: Path, hide_dirs: list[str]) -> list[str]:
    """Argv up to, but not including, the command. Preflight and the real call share this."""
    argv = [bwrap, *merged_usr_args(), "--ro-bind", "/etc", "/etc", "--tmpfs", home]
    # CANARY_CONTROL_INSERT: production binds nothing between the HOME tmpfs and the
    # workspace binds. A RED mutant inserts
    #   --ro-bind $HOME/canary.txt $HOME/canary.txt --ro-bind $HOME/.ssh $HOME/.ssh
    # on the next line and nowhere else.
    argv += [
        "--ro-bind", str(py312), str(py312),
        "--ro-bind", str(harness), str(harness),
        "--ro-bind", str(runs), str(runs),
        "--bind", str(ws), str(ws),
        "--ro-bind", str(state), str(state),
        "--tmpfs", "/tmp",
        "--tmpfs", "/run",
    ]
    for extra in hide_dirs:
        argv += ["--tmpfs", extra]
    # /var is not bound, so a host /var/run is not inside the sandbox.
    argv += [
        "--dev", "/dev",
        "--proc", "/proc",
        "--unshare-net",
        "--unshare-pid",
        "--die-with-parent",
        "--chdir", str(ws),
    ]
    return argv


def _sweep_one(ws: Path) -> None:
    chmod = subprocess.run(
        ["chmod", "-R", "-P", "u+rwX", "--", str(ws)],
        capture_output=True, text=True,
    )
    if chmod.returncode != 0:
        die(f"BLOCKED: sweep failed {ws}")
    found = subprocess.run(
        ["find", "-P", str(ws), "-xdev", "-type", "s", "-delete"],
        capture_output=True, text=True,
    )
    if found.returncode != 0:
        die(f"BLOCKED: sweep failed {ws}")


def finished_workspaces(runs: Path, current: Path) -> list[Path]:
    root = runs / "tmp"
    if not root.is_dir():
        return []
    out = []
    current_real = os.path.realpath(current)
    for entry in os.scandir(root):
        try:
            st = os.lstat(entry.path)
        except OSError:
            continue
        if stat.S_ISLNK(st.st_mode):
            print(f"sweep: skip symlink {entry.path}", file=sys.stderr)
            continue
        if not stat.S_ISDIR(st.st_mode):
            print(f"sweep: skip non-directory {entry.path}", file=sys.stderr)
            continue
        if os.path.realpath(entry.path) == current_real:
            continue
        out.append(Path(entry.path))
    return out


def _workspace_from_cmd(cmd: list[str], fallback: str | None) -> Path | None:
    if fallback:
        return Path(fallback)
    if "--dir" in cmd:
        i = cmd.index("--dir")
        if i + 1 < len(cmd):
            return Path(cmd[i + 1])
    return None


def _parse_cli(argv: list[str]) -> dict:
    out: dict = {
        "expose": [],
        "allow": [],
        "heldout": None,
        "hide": [],
        "harness": None,
        "runs": None,
        "state": None,
        "py312": None,
        "ws": None,
        "cap": 120.0,
        "mount_timeout": 30.0,
        "real_bun": None,
        "cmd": [],
        "mode": None,
        "sock": None,
        "log": None,
        "call": None,
    }
    i = 0
    while i < len(argv):
        a = argv[i]
        nxt = argv[i + 1] if i + 1 < len(argv) else None
        if a == "--":
            out["cmd"] = argv[i + 1 :]
            break
        if nxt is None and a.startswith("--"):
            die(f"unknown argument {a}")
        if a == "--mode":
            out["mode"] = nxt
            i += 2
            continue
        if a == "--expose":
            out["expose"] = [int(p) for p in nxt.split(",") if p]
            i += 2
            continue
        if a == "--allow":
            out["allow"] = [int(p) for p in nxt.split(",") if p]
            i += 2
            continue
        if a == "--heldout":
            out["heldout"] = nxt
            i += 2
            continue
        if a == "--hide-dir":
            out["hide"].append(nxt)
            i += 2
            continue
        if a == "--harness":
            out["harness"] = nxt
            i += 2
            continue
        if a == "--runs":
            out["runs"] = nxt
            i += 2
            continue
        if a == "--state":
            out["state"] = nxt
            i += 2
            continue
        if a == "--py312":
            out["py312"] = nxt
            i += 2
            continue
        if a == "--ws":
            out["ws"] = nxt
            i += 2
            continue
        if a == "--preflight-cap":
            out["cap"] = float(nxt)
            i += 2
            continue
        if a == "--mount-timeout":
            out["mount_timeout"] = float(nxt)
            i += 2
            continue
        if a == "--real-bun":
            out["real_bun"] = nxt
            i += 2
            continue
        if a == "--sock":
            out["sock"] = nxt
            i += 2
            continue
        if a == "--log":
            out["log"] = nxt
            i += 2
            continue
        if a == "--call":
            out["call"] = nxt
            i += 2
            continue
        die(f"unknown argument {a}")
    return out


def _http_meta(head: bytes, body: bytes) -> str:
    lines = head.decode("latin1", "replace").split("\r\n")
    method, path = "", ""
    if lines and lines[0]:
        bits = lines[0].split()
        if bits:
            method = bits[0]
        if len(bits) > 1:
            path = bits[1]
    model = temp = seed = None
    try:
        obj = json.loads(body.decode("utf-8") or "null")
    except (json.JSONDecodeError, UnicodeError):
        obj = None
    if isinstance(obj, dict):
        if "model" in obj:
            model = obj["model"]
        if "temperature" in obj:
            temp = obj["temperature"]
        if "seed" in obj:
            seed = obj["seed"]
    parts = [method, path]
    if model is not None:
        parts.append(f"model={model}")
    if temp is not None:
        shown = int(temp) if isinstance(temp, float) and temp.is_integer() else temp
        if isinstance(temp, int):
            shown = temp
        parts.append(f"temperature: {shown}")
    if seed is not None:
        shown = int(seed) if isinstance(seed, float) and seed.is_integer() else seed
        parts.append(f"seed: {shown}")
    parts.append(f"bytes_in={len(head) + len(body)}")
    return " ".join(p for p in parts if p)


def _read_http(rest: bytes, conn: socket.socket) -> tuple[bytes, bytes]:
    data = rest
    while b"\r\n\r\n" not in data and len(data) < 2_000_000:
        chunk = conn.recv(65536)
        if not chunk:
            break
        data += chunk
    head, _, body = data.partition(b"\r\n\r\n")
    length = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            try:
                length = int(line.split(b":", 1)[1].strip())
            except ValueError:
                length = 0
    while len(body) < length:
        chunk = conn.recv(65536)
        if not chunk:
            break
        body += chunk
    return head, body[:length]


def _splice(left: socket.socket, right: socket.socket) -> int:
    out = 0
    pair = [left, right]
    while True:
        readable, _, _ = select.select(pair, [], [], RELAY_IDLE_S)
        if not readable:
            break
        for src in readable:
            dst = right if src is left else left
            try:
                data = src.recv(65536)
            except OSError:
                return out
            if not data:
                return out
            if src is right:
                out += len(data)
            try:
                dst.sendall(data)
            except OSError:
                return out
    return out


def _die_with_parent() -> None:
    """If the host sandbox is killed, the relay must not keep its pipes open."""
    import ctypes
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
    except OSError:
        return
    if libc.prctl(1, signal.SIGKILL) != 0:  # PR_SET_PDEATHSIG
        return
    if os.getppid() == 1:
        os.kill(os.getpid(), signal.SIGKILL)


def relay_main(sock_path: str, allow: list[int], log_path: str) -> None:
    _die_with_parent()
    allow_set = set(allow)
    path = Path(sock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(sock_path)
    srv.listen(64)
    os.chmod(sock_path, 0o666)

    def log_line(line: str) -> None:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def handle(conn: socket.socket) -> None:
        try:
            buf = b""
            while b"\n" not in buf:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                buf += chunk
                if len(buf) > 8192:
                    return
            line, rest = buf.split(b"\n", 1)
            if line.strip() == b"PROBE":
                conn.sendall(b"OK\n")
                return
            try:
                port = int(line.split()[1])
            except (IndexError, ValueError):
                return
            if port not in allow_set:
                log_line(f"denied port {port}")
                return
            head, body = _read_http(rest, conn)
            try:
                upstream = socket.create_connection(("127.0.0.1", port), timeout=5)
            except OSError:
                log_line(f"denied port {port}")
                return
            try:
                upstream.sendall(head + b"\r\n\r\n" + body)
                sent_back = _splice(conn, upstream)
            finally:
                upstream.close()
            meta = _http_meta(head, body)
            log_line(f"{meta} bytes_out={sent_back}")
        finally:
            try:
                conn.close()
            except OSError:
                pass

    while True:
        try:
            conn, _ = srv.accept()
        except OSError:
            return
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def _probe(sock_path: str, allow: list[int], timeout: float = 5.0) -> bool:
    try:
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.settimeout(timeout)
        conn.connect(sock_path)
        if allow:
            port = allow[0]
            msg = (
                f"PORT {port}\nGET /health HTTP/1.0\r\nHost: 127.0.0.1\r\n"
                "Connection: close\r\n\r\n"
            )
            conn.sendall(msg.encode())
            data = conn.recv(64)
            return bool(data)
        conn.sendall(b"PROBE\n")
        data = conn.recv(16)
        return data.startswith(b"OK")
    except OSError:
        return False
    finally:
        try:
            conn.close()
        except OSError:
            pass


def preflight_mode(call_path: str) -> int:
    spec = json.loads(Path(call_path).read_text(encoding="utf-8"))
    ws = spec["ws"]
    state = spec["state"]
    uid = str(spec["uid"])
    timeout = float(spec["mount_timeout"])
    parent = os.path.dirname(ws)
    while True:
        print(f"WALK {parent}", flush=True)
        for name in BLOCK_NAMES:
            cand = os.path.join(parent, name)
            if os.path.lexists(cand):
                print(f"BLOCKED: opencode-plant {cand}", flush=True)
                return 2
        if parent == "/":
            break
        nxt = os.path.dirname(parent)
        if nxt == parent:
            break
        parent = nxt
    home = os.environ.get("HOME", "")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    extras = ["/etc/opencode", os.path.join(home, ".opencode")]
    if xdg:
        extras.append(os.path.join(xdg, "opencode"))
    for cand in extras:
        print(f"WALK {cand}", flush=True)
        if os.path.lexists(cand):
            print(f"BLOCKED: opencode-plant {cand}", flush=True)
            return 2
    sock_root = os.path.join(state, "r")
    prefix = sock_root.rstrip("/") + "/"
    mounts_text = Path("/proc/self/mounts").read_text(encoding="utf-8", errors="replace")
    for mnt, opts in _parse_mounts(mounts_text):
        if mnt in ("/proc", "/sys") or mnt.startswith("/proc/") or mnt.startswith("/sys/"):
            continue
        ro = "ro" in opts.split(",")
        if ro:
            cmd = [
                "find", mnt, "-xdev",
                "(", "-path", "/proc", "-o", "-path", "/sys", ")", "-prune",
                "-o", "-type", "d", "!", "-user", uid,
                "(", "!", "-executable", "-o", "!", "-readable", ")", "-prune",
                "-o", "-type", "s", "-print",
            ]
        else:
            cmd = [
                "find", mnt, "-xdev",
                "(", "-path", "/proc", "-o", "-path", "/sys", ")", "-prune",
                "-o", "-type", "s", "-print",
            ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"BLOCKED: sandbox-socket timeout {mnt}", flush=True)
            return 2
        if proc.returncode != 0:
            print(f"BLOCKED: sandbox-socket rc={proc.returncode} mount={mnt}", flush=True)
            if proc.stderr:
                print(proc.stderr, file=sys.stderr, flush=True)
            return 2
        for line in proc.stdout.splitlines():
            path = line.strip()
            if path and not path.startswith(prefix):
                print(f"BLOCKED: sandbox-socket {path}", flush=True)
                return 2
    print("PREFLIGHT_OK", flush=True)
    return 0


def _listen(port: int, sock_path: str) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(32)

    def handle(conn: socket.socket) -> None:
        up = None
        try:
            up = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            up.connect(sock_path)
            up.sendall(f"PORT {port}\n".encode())
            _splice(conn, up)
        except OSError:
            pass
        finally:
            conn.close()
            if up is not None:
                up.close()

    while True:
        try:
            conn, _ = srv.accept()
        except OSError:
            return
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def inside_mode(call_path: str) -> int:
    spec = json.loads(Path(call_path).read_text(encoding="utf-8"))
    for port in spec["expose"]:
        threading.Thread(target=_listen, args=(int(port), spec["sock"]), daemon=True).start()
    if spec["expose"]:
        time.sleep(0.05)
    proc = subprocess.run(spec["cmd"])
    return int(proc.returncode)


def _launch(argv: list[str], env: dict[str, str], *, cap: float | None,
            inherit_stdin: bool, cwd: str | None = None):
    stdin = None if inherit_stdin else subprocess.DEVNULL
    proc = subprocess.Popen(
        argv, env=env, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True, cwd=cwd,
    )
    try:
        out, err = proc.communicate(timeout=cap)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
        return None, b"", b""
    return proc.returncode, out or b"", err or b""


def _blocked_line(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("BLOCKED:"):
            return line
    return None


def _refuse_ephemeral_checkout(wt: Path) -> None:
    """The sandbox replaces /tmp and /run. A checkout there would be hidden."""
    real = Path(os.path.realpath(wt))
    for root in ("/tmp", "/run"):
        if real == Path(root) or str(real).startswith(root + os.sep):
            die(f"BLOCKED: checkout under {root}")


def host_main(argv: list[str]) -> int:
    opt = _parse_cli(argv)
    bwrap = shutil.which("bwrap")
    if not bwrap:
        die("bwrap required")
    assert_tools()
    home = os.environ.get("HOME") or str(Path.home())
    wt = _worktree()
    _refuse_ephemeral_checkout(wt)
    harness = Path(opt["harness"] or (wt / "tmp" / "harness2")).resolve()
    if opt["heldout"]:
        runs = Path(opt["runs"] or (wt / "tmp" / "heldout-runs" / opt["heldout"])).resolve()
    else:
        runs = Path(opt["runs"] or (wt / "tmp" / "harness2-runs")).resolve()
    state = Path(opt["state"] or (wt / "tmp" / "state")).resolve()
    cmd = list(opt["cmd"])
    if opt["real_bun"]:
        cmd = [opt["real_bun"], *cmd]
    if not cmd:
        die("missing command")
    ws = _workspace_from_cmd(cmd, opt["ws"])
    if ws is None:
        ws = Path.cwd()
    ws = ws.resolve()
    runs_tmp = (runs / "tmp").resolve()
    if ws.parent != runs_tmp or not ws.is_dir():
        die("workspace is not directly under RUNS/tmp")
    py312 = resolve_py312(opt["py312"], home)
    (state / "r").mkdir(parents=True, exist_ok=True)
    (state / "bin").mkdir(parents=True, exist_ok=True)
    sock = state / "r" / "s"
    if len(str(sock)) > SUN_PATH_MAX:
        die("socket path too long")
    lock_fd = _acquire_call_lock(wt / "tmp" / "host-only")
    try:
        for finished in finished_workspaces(runs, ws):
            _sweep_one(finished)
        env = build_env(os.environ, home=home, state=state, harness=harness)
        call = {
            "ws": str(ws),
            "state": str(state),
            "sock": str(sock),
            "expose": opt["expose"],
            "uid": os.getuid(),
            "mount_timeout": opt["mount_timeout"],
            "cap": opt["cap"],
            "cmd": cmd,
        }
        call_path = state / "bin" / "call.json"
        call_path.write_text(json.dumps(call), encoding="utf-8")
        runner = state / "bin" / "sandbox.py"
        shutil.copyfile(Path(__file__).resolve(), runner)
        os.chmod(runner, 0o755)
        base = build_bwrap(
            bwrap, home=home, harness=harness, runs=runs, ws=ws, state=state,
            py312=py312, hide_dirs=list(opt["hide"]),
        )
        py = "/usr/bin/python3"
        pre_cmd = [py, str(runner), "--mode", "preflight", "--call", str(call_path)]
        real_cmd = [py, str(runner), "--mode", "inside", "--call", str(call_path)]
        log_path = state / "relay.log"
        relay = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--mode", "relay",
             "--sock", str(sock), "--allow", ",".join(str(p) for p in opt["allow"]),
             "--log", str(log_path)],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        (state / "relay.pid").write_text(str(relay.pid), encoding="utf-8")
        try:
            deadline = time.time() + 5
            up = False
            while time.time() < deadline:
                if _probe(str(sock), opt["allow"], timeout=1):
                    up = True
                    break
                if relay.poll() is not None:
                    break
                time.sleep(0.05)
            if not up:
                die("relay down")
            rc, out, err = _launch(
                base + ["--", *pre_cmd], env, cap=opt["cap"], inherit_stdin=False, cwd=str(ws),
            )
            text = (out + err).decode("utf-8", "replace")
            (state / "plant-walk.txt").write_text(text, encoding="utf-8")
            if rc is None:
                die("BLOCKED: preflight cap")
            blocked = _blocked_line(text)
            if blocked or rc != 0:
                die(blocked or f"BLOCKED: preflight rc={rc}")
            real = subprocess.Popen(
                base + ["--", *real_cmd], env=env, stdin=None, start_new_session=True,
                cwd=str(ws),
            )
            (state / "call.pgid").write_text(str(real.pid), encoding="utf-8")
            dead = threading.Event()
            stop = threading.Event()

            def watch() -> None:
                misses = 0
                while not stop.is_set() and real.poll() is None:
                    if _probe(str(sock), opt["allow"]):
                        misses = 0
                        stop.wait(WATCHDOG_GAP_S)
                        continue
                    misses += 1
                    if misses >= 2:
                        dead.set()
                        try:
                            os.killpg(real.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        return
                    stop.wait(WATCHDOG_GAP_S)

            threading.Thread(target=watch, daemon=True).start()
            child_rc = real.wait()
            stop.set()
            if dead.is_set():
                die("relay down")
            return int(child_rc)
        finally:
            try:
                os.killpg(relay.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                relay.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(relay.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if ws.is_dir():
                try:
                    _sweep_one(ws)
                except SystemExit:
                    raise
    finally:
        os.close(lock_fd)


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--mode"] or (argv and "--mode" in argv[:6]):
        opt = _parse_cli(argv)
        if opt["mode"] == "relay":
            relay_main(opt["sock"], opt["allow"], opt["log"])
            return
        if opt["mode"] == "preflight":
            raise SystemExit(preflight_mode(opt["call"]))
        if opt["mode"] == "inside":
            raise SystemExit(inside_mode(opt["call"]))
        die(f"unknown mode {opt['mode']}")
    rc = host_main(argv)
    if rc:
        # Child failures stay the child's code. Policy failures already exited via die().
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
