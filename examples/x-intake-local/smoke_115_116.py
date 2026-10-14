#!/usr/bin/env python3
"""Operate-or-FAIL smokes for X intake Entries 115-116 (OpenQodex, assay). Stdlib only.

Usage: python3 examples/x-intake-local/smoke_115_116.py --entry openqodex|assay

Same contract and receipts as smoke.py next to it (whose helpers it reuses): exit 0 = PASS, 1 = the tool ran but
the check failed, 2 = can't run here (prereq missing; reason recorded). Writes pipelines/smoke/<entry>/latest.json.
Never installs anything; scratch goes to a fresh tempfile directory that is removed. Tool subprocesses get an env with
only PATH/HOME/TERM/LANG/NO_COLOR (plus TMPDIR / PLAYWRIGHT_BROWSERS_PATH where named below); no provider keys.
No smoke calls a model. PFY_XINTAKE_TIMEOUT (float seconds, > 0) overrides the 600s per-command timeout.

  openqodex $OPENQODEX_DIR, then ~/DEVELOP/pfy-mentat/tmp/openqodex (an `npm install --prefix <dir> --ignore-scripts
            openqodex@0.12.0`), package version pinned ($OPENQODEX_VERSION overrides). Node >= 22 from
            $OPENQODEX_NODE, ~/DEVELOP/pfy-mentat/tmp/openqodex/node/bin/node, or PATH; older Node exits 2.
            HOME is $OPENQODEX_HOME or ~/DEVELOP/pfy-mentat/tmp/openqodex/home, kept between runs because the first
            review downloads its scanners (semgrep, gitleaks, ruff, bandit; about 360 MB) into it; that first run
            needs network. Exits 2 if `claude` or `codex` is on the tool PATH, so no reviewer model can start.
            In a scratch git repo with a planted `subprocess.call(cmd, shell=True)`: `review` must say
            "Full review unavailable" and list a semgrep or bandit candidate on that line; `review --agent` must
            print a brief with the candidate ids and a findings path; `review --finalize` must accept a findings file
            that raises the shell=True candidate and drops the rest, and reject one whose `source` is made up.
            The real HOME's ~/.openqodex, ~/.claude, ~/.codex and ~/.cursor must not change.
  assay     $ASSAY_BIN, then ~/DEVELOP/pfy-mentat/tmp/assay/venv/bin/assay (a venv with `pip install
            assay-ui==0.3.0`), then PATH; `assay --version` pinned to 0.3.0 ($ASSAY_VERSION overrides). Chromium from
            $PLAYWRIGHT_BROWSERS_PATH or ~/DEVELOP/pfy-mentat/tmp/assay/ms-playwright (must hold a
            chromium_headless_shell-* build, else exit 2; the smoke never lets assay download one). Runs under bwrap
            with a read-only root and no network when it works. A working counter page must pass (exit 0, works,
            0 failed); a page whose button throws must fail (nonzero, a case naming the error, the repeat grouped as
            "same finding"). Records, without failing, whether a button that does nothing is flagged
            (`dead_button_flagged`).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from smoke import TMP, write

OPENQODEX_PIN = "0.12.0"
ASSAY_PIN = "0.3.0"

PLANTED = ("import subprocess\nimport sys\n\n\ndef run(cmd):\n    return subprocess.call(cmd, shell=True)\n\n\n"
           "run(sys.argv[1])\n")
PLANTED_LINE = 6
GOOD_PAGE = ("<!doctype html><html><body><h1>Counter</h1><p id=\"n\">0</p><button id=\"inc\" onclick=\""
             "document.getElementById('n').textContent=+document.getElementById('n').textContent+1\">Add one</button>"
             "</body></html>\n")
THROW_PAGE = ("<!doctype html><html><body><h1>Counter</h1><p id=\"n\">0</p>"
              "<button id=\"inc\" onclick=\"undefinedFn()\">Add one</button></body></html>\n")
DEAD_PAGE = ("<!doctype html><html><body><h1>Counter</h1><p id=\"n\">0</p>"
             "<button id=\"inc\" onclick=\"void 0\">Add one</button></body></html>\n")


def tmo() -> float:
    try:
        v = float(os.environ.get("PFY_XINTAKE_TIMEOUT", ""))
        return v if v > 0 else 600.0
    except ValueError:
        return 600.0


def clean_env(home: str, path: str, **extra: str) -> dict:
    e = {"HOME": home, "PATH": path, "TERM": "dumb", "LANG": "C.UTF-8", "NO_COLOR": "1"}
    e.update(extra)
    return e


def bwrap_ok() -> bool:
    b = shutil.which("bwrap")
    if not b:
        return False
    try:
        return subprocess.run([b, "--ro-bind", "/", "/", "--dev", "/dev", "--unshare-net", "true"],
                              capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


def wrap(cmd: list[str], writable: list[str], use_bwrap: bool) -> list[str]:
    if not use_bwrap:
        return cmd
    w = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--unshare-net", "--die-with-parent"]
    for d in writable:
        w += ["--bind", d, d]
    return w + cmd


def sh(cmd, env, cwd=None):
    return subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True, timeout=tmo(),
                          stdin=subprocess.DEVNULL)


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


def node_major(node: str) -> tuple[int, str]:
    try:
        v = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as e:
        return 0, f"node not runnable: {e}"
    m = re.match(r"v(\d+)\.", v)
    return (int(m[1]) if m else 0), v


def smoke_openqodex(r: dict) -> int:
    d = next((Path(c) for c in (os.environ.get("OPENQODEX_DIR"), str(TMP / "openqodex"))
              if c and (Path(c) / "node_modules/openqodex/dist/bin.js").is_file()), None)
    if not d:
        r["reason"] = ("openqodex not staged: npm install --prefix ~/DEVELOP/pfy-mentat/tmp/openqodex --ignore-scripts "
                       f"openqodex@{OPENQODEX_PIN} (or set $OPENQODEX_DIR)")
        return 2
    pkg = d / "node_modules/openqodex"
    ver = json.loads((pkg / "package.json").read_text()).get("version")
    r["version"] = ver
    want = os.environ.get("OPENQODEX_VERSION") or OPENQODEX_PIN
    if ver != want:
        r["reason"] = f"openqodex {ver} != pinned {want} ($OPENQODEX_VERSION overrides)"
        return 2
    node = next((c for c in (os.environ.get("OPENQODEX_NODE"), str(d / "node/bin/node"), shutil.which("node"))
                 if c and Path(c).is_file()), None)
    major, nv = node_major(node) if node else (0, "no node")
    r["node"] = nv
    if major < 22:
        r["reason"] = (f"Node >= 22 needed, found {nv}; unpack the nodejs.org latest-v22.x linux-x64 tarball "
                       "(checked against SHASUMS256.txt) as ~/DEVELOP/pfy-mentat/tmp/openqodex/node or set $OPENQODEX_NODE")
        return 2
    tool_path = f"{Path(node).parent}:/usr/bin:/bin"
    for rv in ("claude", "codex"):
        if shutil.which(rv, path=tool_path):
            r["reason"] = f"`{rv}` is on the tool PATH; refusing, since a review would start a model"
            return 2
    home = Path(os.environ.get("OPENQODEX_HOME") or (d / "home"))
    home.mkdir(parents=True, exist_ok=True)
    r["home"] = str(home)
    r["containment"] = "unwrapped (first run downloads scanners); HOME under tmp/, real-HOME dirs checked"
    real = [Path.home() / n for n in (".openqodex", ".claude", ".codex", ".cursor")]
    if home.resolve() == Path.home().resolve():
        r["reason"] = "OPENQODEX_HOME must not be the real HOME"
        return 2
    before = [tree_sig(p) for p in real]
    env = clean_env(str(home), tool_path)
    q = [node, str(pkg / "dist/bin.js")]
    with tempfile.TemporaryDirectory(prefix="pfy-openqodex-") as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        g = lambda *a: sh(["git", "-c", "user.email=smoke@local", "-c", "user.name=smoke", *a], env, cwd=repo)
        g("init", "-q", "-b", "main")
        (repo / "app.py").write_text('print("hi")\n')
        g("add", ".")
        g("commit", "-qm", "init")
        (repo / "app.py").write_text(PLANTED)
        p = sh(q + ["review"], env, cwd=repo)
        out = p.stdout + p.stderr
        r["review_exit"] = p.returncode
        if "Full review unavailable" not in out:
            r["reason"] = f"`review` did not report the missing reviewer: {out[-400:]}"
            return 1
        cands = sorted(repo.glob(".openqodex/reviews/*/unchecked-candidates.json"))
        if not cands:
            r["reason"] = f"no unchecked-candidates.json after `review`: {out[-400:]}"
            return 1
        cl = json.loads(cands[-1].read_text()).get("candidates", [])
        r["scanner_candidates"] = [f"{c.get('source')}:{c.get('ruleId')}@{c.get('lineStart')}" for c in cl]
        if not any(c.get("source") in ("semgrep", "bandit") and str(c.get("lineStart")) == str(PLANTED_LINE)
                   for c in cl):
            r["reason"] = "no semgrep or bandit candidate on the planted shell=True line"
            return 1
        p = sh(q + ["review", "--agent"], env, cwd=repo)
        brief = p.stdout
        m_path = re.search(r"Write the JSON to `([^`]+agent-findings\.json)`", brief)
        m_cid = re.search(r"- Change: ([0-9a-f]{12})", brief)
        items = re.findall(r"^- (c\d+) \[([^\]]+)\] ([^:\s]+):(\d+)", brief, re.M)
        if p.returncode != 0 or not (m_path and m_cid and items):
            r["reason"] = f"`review --agent` gave no usable brief (exit {p.returncode}): {(p.stdout + p.stderr)[-400:]}"
            return 1
        raise_ = next((i for i in items if i[3] == str(PLANTED_LINE) and "shell" in i[1].lower() + i[0]), None) \
            or next((i for i in items if i[3] == str(PLANTED_LINE)), None)
        if not raise_:
            r["reason"] = "brief lists no candidate on the planted line"
            return 1
        good = {"version": 1, "change_id": m_cid[1], "summary": "Runs a command-line argument through a shell.",
                "reviewer": "subagent",
                "findings": [{"severity": "major", "category": "security", "confidence": 0.9, "file_path": "app.py",
                              "line_number": PLANTED_LINE, "line_end": PLANTED_LINE, "title": "Shell injection from argv",
                              "description": "cmd comes from argv and runs with shell=True. Pass a list instead.",
                              "suggested_change": None, "source": raise_[1], "candidate": raise_[0]}],
                "dropped": [{"candidate": i[0], "reason": "covered by the raised finding or style"}
                            for i in items if i[0] != raise_[0]]}
        fpath = Path(m_path[1])
        fpath.write_text(json.dumps(good))
        p = sh(q + ["review", "--finalize", "--cwd", str(repo), str(fpath)], env, cwd=repo)
        r["finalize_good"] = (p.returncode, (p.stdout + p.stderr).strip().splitlines()[:1])
        if p.returncode != 0 or "Shell injection from argv" not in p.stdout + p.stderr:
            r["reason"] = f"finalize rejected a valid findings file: {(p.stdout + p.stderr)[-400:]}"
            return 1
        bad = dict(good, findings=[dict(good["findings"][0], source="made-up")], dropped=[])
        bpath = fpath.with_name("bad-findings.json")
        bpath.write_text(json.dumps(bad))
        p = sh(q + ["review", "--finalize", "--cwd", str(repo), str(bpath)], env, cwd=repo)
        r["finalize_bad_exit"] = p.returncode
        if p.returncode == 0:
            r["reason"] = "finalize accepted a finding with a made-up source"
            return 1
    if [tree_sig(p) for p in real] != before:
        r["reason"] = "real HOME ~/.openqodex, ~/.claude, ~/.codex or ~/.cursor changed"
        return 1
    r["reason"] = ("no reviewer reported, scanner candidate on the planted line, agent brief issued, "
                   "finalize accepted valid findings and rejected a made-up source")
    return 0


def run_assay(binary: str, page: str, td: str, browsers: str, ub: bool) -> tuple[int, dict | None, str]:
    site = Path(td) / page
    env = clean_env(td, "/usr/bin:/bin", TMPDIR=td, PLAYWRIGHT_BROWSERS_PATH=browsers)
    p = sh(wrap([binary, str(site), "--json"], [td], ub), env)
    try:
        return p.returncode, json.loads(p.stdout), p.stderr
    except ValueError:
        return p.returncode, None, (p.stdout + p.stderr)[-400:]


def smoke_assay(r: dict) -> int:
    b = next((c for c in (os.environ.get("ASSAY_BIN"), str(TMP / "assay/venv/bin/assay"), shutil.which("assay"))
              if c and Path(c).is_file()), None)
    if not b:
        r["reason"] = ("assay not staged: python3 -m venv ~/DEVELOP/pfy-mentat/tmp/assay/venv && "
                       f"~/DEVELOP/pfy-mentat/tmp/assay/venv/bin/pip install assay-ui=={ASSAY_PIN} (or set $ASSAY_BIN)")
        return 2
    v = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
    r["version"] = v
    want = os.environ.get("ASSAY_VERSION") or ASSAY_PIN
    if v.split()[-1:] != [want]:
        r["reason"] = f"assay version {v!r} != pinned {want} ($ASSAY_VERSION overrides)"
        return 2
    browsers = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or str(TMP / "assay/ms-playwright")
    if not list(Path(browsers).glob("chromium_headless_shell-*")):
        r["reason"] = (f"no Chromium under {browsers}; stage it once with PLAYWRIGHT_BROWSERS_PATH={browsers} "
                       "~/DEVELOP/pfy-mentat/tmp/assay/venv/bin/playwright install chromium (the smoke never downloads)")
        return 2
    ub = bwrap_ok()
    r["containment"] = "bwrap read-only root, no network" if ub else "temp HOME and TMPDIR only (no bwrap)"
    with tempfile.TemporaryDirectory(prefix="pfy-assay-") as td:
        for name, html in (("good", GOOD_PAGE), ("throw", THROW_PAGE), ("dead", DEAD_PAGE)):
            (Path(td) / name).mkdir()
            (Path(td) / name / "index.html").write_text(html)
        code, d, err = run_assay(b, "good", td, browsers, ub)
        if d is None or code != 0 or not d.get("works") or d.get("failed") != 0:
            r["reason"] = f"working page did not pass (exit {code}): {err[-300:] if d is None else d.get('failed')}"
            return 1
        r["good"] = {"planned": d.get("planned"), "passed": d.get("passed")}
        code, d, err = run_assay(b, "throw", td, browsers, ub)
        if d is None or code == 0 or d.get("works") or not d.get("failed"):
            r["reason"] = f"page whose button throws was not flagged (exit {code})"
            return 1
        details = " ".join(c.get("detail", "") for c in d.get("cases", []))
        if "undefinedFn" not in details:
            r["reason"] = "flagged case does not name the thrown error"
            return 1
        if not any(lk.get("kind") == "same" for lk in d.get("links", [])):
            r["reason"] = "repeat of the same failure was not grouped as 'same finding'"
            return 1
        r["throw"] = {"exit": code, "failed": d.get("failed")}
        code, d, err = run_assay(b, "dead", td, browsers, ub)
        r["dead_button_flagged"] = None if d is None else bool(d.get("failed"))
    r["reason"] = "working page passed; throwing button flagged with the error and grouped repeat"
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", required=True, choices=["openqodex", "assay"])
    a = ap.parse_args()
    receipt = {"entry": a.entry, "script": "examples/x-intake-local/smoke_115_116.py",
               "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    fn = {"openqodex": smoke_openqodex, "assay": smoke_assay}[a.entry]
    try:
        code = fn(receipt)
    except subprocess.TimeoutExpired as e:
        receipt["reason"] = f"timeout after {e.timeout}s: {e.cmd[:3] if isinstance(e.cmd, list) else e.cmd}"
        code = 1
    return write(a.entry, receipt, code)


if __name__ == "__main__":
    sys.exit(main())
