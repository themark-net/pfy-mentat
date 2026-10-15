#!/usr/bin/env python3
"""Operate-or-FAIL smokes for X intake Entries 117-118 (Kander, Moira). Stdlib only.

Usage: python3 examples/x-intake-local/smoke_117_118.py --entry kander|moira

Same contract and receipts as smoke.py next to it (whose helpers it reuses): exit 0 = PASS, 1 = the tool ran but
the check failed, 2 = can't run here (prereq missing; reason recorded). Writes pipelines/smoke/<entry>/latest.json.
Never installs or downloads anything. Every child process starts through `run_isolated` in smoke.py (fresh temp HOME,
env limited to PATH/HOME/TERM/LANG/NO_COLOR plus the variables named below; nothing copied from this process; a
timeout SIGKILLs the process group). No provider keys. No smoke calls a model or starts an agent.
PFY_XINTAKE_TIMEOUT (float seconds, > 0) overrides the 600s per-command timeout.

  kander  $KANDER_BIN, then ~/DEVELOP/pfy-mentat/tmp/kander/kander (the release tarball kander-linux-amd64.tar.gz
          unpacked there), then PATH. `kander version` pinned to 0.9.5 ($KANDER_VERSION overrides) and the binary's
          sha256 pinned to the v0.9.5 linux-amd64 build ($KANDER_SHA256 overrides; set it to "skip" to only check
          the version). Runs with a fresh temp HOME and GH_CONFIG_DIR (so no gh login is seen), PATH=/usr/bin:/bin and the
          git identity variables, under bwrap with a read-only root and no network when it works. In a scratch git repo: `doctor` must print
          its environment check and agent table (its exit code is recorded, not required: it is nonzero when no
          agent CLI is installed); `init .` must create kanban/ and add /kanban/ to .git/info/exclude; `new chore`
          must create one backlog card; `ls` must list it; `show --json` must report State "backlog"; `check` must
          print "ok: 1 tasks"; `show` of an unknown id must exit nonzero. No `start`, `pick`, `orchestrate` or
          `review` (those launch agents). The real HOME's ~/.agents/kander and ~/.config/kander must not change.
          Records which agents doctor detected (`agents_detected`) without failing.
  moira   $MOIRA_DIR, then ~/DEVELOP/pfy-mentat/tmp/moira, holding upstream's docker-compose.yml,
          config/traefik-self-host.yml and an operator-made .env (never committed; the smoke never reads or prints
          its secrets). Needs docker ($DOCKER_BIN, ~/DEVELOP/pfy-mentat/tmp/docker/docker, or
          PATH) with the compose plugin; exit 2 without them. The image must be pinned by digest:
          $MOIRA_IMAGE, or MOIRA_IMAGE in the .env, must contain "@sha256:" (upstream defaults to :latest), else exit 2.
          Passes only MOIRA_PORT and MOIRA_IMAGE to compose (no bwrap: it needs the docker socket). Brings the
          stack up as compose project "pfy-moira-smoke" on $MOIRA_PORT (default 18080), waits up to the
          timeout for the ingress, then GET /docs/ must be 200 and POST /mcp (an MCP initialize with no login) must
          answer with an HTTP status (recorded as `mcp_status`; 401/403 is fine). Always runs `compose down` after.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from smoke import TMP, find_bin, pinned, run_isolated, timeout_reason, write

KANDER_PIN = "0.9.5"
KANDER_SHA = "3a5f8979f94fc1325dbcf9aa30e73831d1db907302c13b5273362313c327e254"  # v0.9.5 kander-linux-amd64
GIT_ID = {"GIT_AUTHOR_NAME": "pfy-smoke", "GIT_AUTHOR_EMAIL": "smoke@localhost",
          "GIT_COMMITTER_NAME": "pfy-smoke", "GIT_COMMITTER_EMAIL": "smoke@localhost"}


def tmo() -> float:
    try:
        v = float(os.environ.get("PFY_XINTAKE_TIMEOUT", ""))
        return v if v > 0 else 600.0
    except ValueError:
        return 600.0


def tree_sig(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        try:
            st = f.stat()
            h.update(f"{f}:{st.st_size}:{st.st_mtime_ns}".encode())
        except OSError:
            pass
    return h.hexdigest()


def smoke_kander(r: dict) -> int:
    b = find_bin("KANDER_BIN", "kander/kander", "kander")
    if not b:
        r["reason"] = ("kander not found: set $KANDER_BIN or unpack kander-linux-amd64.tar.gz (v0.9.5) into "
                       "~/DEVELOP/pfy-mentat/tmp/kander/")
        return 2
    r["binary"] = b
    want_sha = pinned(r, "KANDER_SHA256", KANDER_SHA, lower=True)
    got_sha = hashlib.sha256(Path(b).read_bytes()).hexdigest()
    r["sha256"] = got_sha
    if want_sha != "skip" and got_sha != want_sha:
        r["reason"] = f"kander sha256 {got_sha[:12]} is not the expected {want_sha[:12]} (set $KANDER_SHA256)"
        return 2
    want_v = pinned(r, "KANDER_VERSION", KANDER_PIN)
    real_home = Path.home()
    watched = (".agents/kander", ".config/kander")
    before = {d: tree_sig(real_home / d) for d in watched}
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="pfy-kander-") as td:
        home, repo = Path(td, "home"), Path(td, "repo")
        home.mkdir()
        repo.mkdir()
        extra = {"GH_CONFIG_DIR": str(home / ".config/gh"), **GIT_ID}

        def run(argv: list[str], tag: str) -> subprocess.CompletedProcess:
            try:
                return run_isolated(argv, home=str(home), cwd=str(repo), timeout=tmo(), extra=extra,
                                    bwrap_writable=[td])
            except subprocess.TimeoutExpired:
                raise TimeoutError(timeout_reason(tag))

        def k(*args: str) -> subprocess.CompletedProcess:
            return run([b, "--lang", "en", *args], f"kander {args[0]}")

        v = k("version")
        r["version_out"] = (v.stdout + v.stderr).strip()[:200]
        if v.returncode != 0 or want_v not in v.stdout:
            r["reason"] = f"kander version is not {want_v}: {r['version_out']!r} (set $KANDER_VERSION)"
            return 2
        g = run(["git", "init", "-q"], "git init")
        g2 = run(["git", "commit", "-q", "--allow-empty", "-m", "init"], "git commit")
        if g.returncode or g2.returncode:
            r["reason"] = f"git scratch repo failed: {(g.stderr + g2.stderr).strip()[:200]}"
            return 2
        d = k("doctor")
        out = d.stdout + d.stderr
        # doctor exits nonzero when no agent CLI is installed, which is normal for a smoke; require the report only
        checks["doctor_report"] = "Kander environment check" in out and "Agent capabilities" in out
        r["doctor_rc"] = d.returncode
        r["agents_detected"] = re.findall(r"\[OK\] (\w+): \S+ \(", out)
        r["doctor_tail"] = out.strip().splitlines()[-12:]
        i = k("init", ".")
        excl = repo / ".git/info/exclude"
        checks["init_ok"] = (i.returncode == 0 and (repo / "kanban/backlog").is_dir()
                             and excl.exists() and "/kanban/" in excl.read_text())
        n = k("new", "chore", "smoke-card", "Smoke card")
        checks["new_ok"] = n.returncode == 0 and "backlog" in n.stdout
        ls = k("ls")
        m = re.search(r"backlog\s+\S+\s+\S+\s+(\S+-task)\s+Smoke card", ls.stdout)
        checks["ls_ok"] = ls.returncode == 0 and bool(m)
        tid = m[1] if m else "missing-task"
        r["task_id"] = tid
        s = k("show", "--json", tid)
        try:
            state = json.loads(s.stdout)["entry"]["State"]
        except (ValueError, KeyError, TypeError):
            state = None
        checks["show_backlog"] = s.returncode == 0 and state == "backlog"
        c = k("check")
        checks["check_ok"] = c.returncode == 0 and "ok: 1 tasks" in c.stdout
        bad = k("show", "--json", "no-such-task")
        checks["unknown_id_nonzero"] = bad.returncode != 0
    after = {d: tree_sig(real_home / d) for d in watched}
    checks["real_home_untouched"] = before == after
    r["checks"] = checks
    failed = [x for x, ok in checks.items() if not ok]
    if failed:
        r["reason"] = f"failed checks: {', '.join(failed)}"
        return 1
    r["reason"] = "board init, card create/list/show/check all worked in a temp HOME; no agent started"
    return 0


def http(method: str, url: str, body: bytes | None = None, headers: dict | None = None) -> int:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def smoke_moira(r: dict) -> int:
    d = Path(os.environ.get("MOIRA_DIR") or (TMP / "moira"))
    r["dir"] = str(d)
    need = [d / "docker-compose.yml", d / "config/traefik-self-host.yml", d / ".env"]
    missing = [str(p) for p in need if not p.exists()]
    if missing:
        r["reason"] = f"Moira compose dir not staged (missing {', '.join(missing)}); see the handoff"
        return 2
    docker = find_bin("DOCKER_BIN", "docker/docker", "docker")
    if not docker:
        r["reason"] = "docker is not available"
        return 2
    path = f"{Path(docker).parent}:/usr/bin:/bin"
    image = os.environ.get("MOIRA_IMAGE", "").strip()
    if not image:
        for line in (d / ".env").read_text().splitlines():
            if line.startswith("MOIRA_IMAGE="):
                image = line.split("=", 1)[1].strip()
    r["image"] = image
    if "@sha256:" not in image:
        r["reason"] = "MOIRA_IMAGE is not pinned by digest (upstream defaults to :latest); set it to <image>@sha256:..."
        return 2
    port = os.environ.get("MOIRA_PORT", "18080")
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="pfy-moira-") as home:
        extra = {"MOIRA_PORT": port, "MOIRA_IMAGE": image}

        def dc(*args: str, tag: str) -> subprocess.CompletedProcess:
            try:
                return run_isolated([docker, "compose", "-p", "pfy-moira-smoke", *args], home=home, cwd=str(d),
                                    timeout=tmo(), path=path, extra=extra, bwrap_writable=None)
            except subprocess.TimeoutExpired:
                raise TimeoutError(timeout_reason(tag))

        if dc("version", tag="docker compose version").returncode != 0:
            r["reason"] = "the docker compose plugin is not available"
            return 2
        try:
            up = dc("up", "-d", tag="docker compose up")
            r["up_tail"] = (up.stdout + up.stderr).strip().splitlines()[-6:]
            if up.returncode != 0:
                r["reason"] = "docker compose up failed"
                return 1
            deadline = time.time() + min(tmo(), 300)
            docs = 0
            while time.time() < deadline:
                docs = http("GET", f"http://127.0.0.1:{port}/docs/")
                if docs == 200:
                    break
                time.sleep(3)
            checks["docs_200"] = docs == 200
            init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                               "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                                          "clientInfo": {"name": "pfy-smoke", "version": "0"}}}).encode()
            st = http("POST", f"http://127.0.0.1:{port}/mcp", init,
                      {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
            r["mcp_status"] = st
            checks["mcp_answers"] = st != 0
        finally:
            r["down_rc"] = dc("down", tag="docker compose down").returncode
    r["checks"] = checks
    failed = [x for x, ok in checks.items() if not ok]
    if failed:
        r["reason"] = f"failed checks: {', '.join(failed)}"
        return 1
    r["reason"] = "self-host stack came up on a digest-pinned image; /docs/ served and /mcp answered"
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", required=True, choices=["kander", "moira"])
    a = ap.parse_args()
    receipt = {"entry": a.entry, "script": "examples/x-intake-local/smoke_117_118.py",
               "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    fn = {"kander": smoke_kander, "moira": smoke_moira}[a.entry]
    try:
        code = fn(receipt)
    except TimeoutError as e:
        receipt["reason"] = str(e)
        code = 1
    return write(a.entry, receipt, code)


if __name__ == "__main__":
    sys.exit(main())
