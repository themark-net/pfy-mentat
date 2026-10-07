#!/usr/bin/env python3
"""Operate-or-FAIL smokes for X intake Entries 095-097 (Qwen3.8-Flash-Next, Sandlock, Foremerge). Stdlib only.

Usage: python3 examples/x-intake-local/smoke.py --entry qwen38flash|sandlock|foremerge

Exit 0 = PASS. 1 = the tool ran but the check failed. 2 = can't run here (prereq missing; reason recorded).
Writes pipelines/smoke/<entry>/latest.json every time. Never installs anything, never downloads into the repo,
and every scratch file goes to a fresh tempfile directory that is removed afterwards.

  qwen38flash  $QWEN38_URL = an OpenAI-compatible base URL (e.g. http://127.0.0.1:8080/v1 from llama-server)
               already serving a Qwen3.8-Flash-Next GGUF. Asks for an exact token and checks it comes back.
               Never starts a server or loads a model itself (nimo memory edge: see Entries 089-094).
  sandlock     $SANDLOCK_BIN or ~/DEVELOP/pfy-mentat/tmp/sandlock/sandlock or `sandlock` on PATH; Linux 6.12+.
               Runs /bin/sh confined to one writable dir and expects the allowed write to land and a write to a
               sibling dir to be refused.
  foremerge    $FOREMERGE_BIN or ~/DEVELOP/pfy-mentat/tmp/foremerge/foremerge or `foremerge` on PATH.
               In a throwaway git repo: publish "replace symbol:PaymentService", then preflight
               "extend symbol:PaymentService" and expect a HIGH conflict; an unrelated scope must not conflict.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TMP = Path.home() / "DEVELOP/pfy-mentat/tmp"


def write(entry: str, receipt: dict, code: int) -> int:
    receipt["exit_code"] = code
    receipt["verdict"] = {0: "PASS", 1: "FAIL", 2: "FAIL_CANNOT_RUN_HERE"}[code]
    out = ROOT / "pipelines/smoke" / entry / "latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: receipt.get(k) for k in ("verdict", "reason")}, ensure_ascii=False))
    print(f"receipt: {out}")
    return code


def run(cmd: list[str], cwd: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def find_bin(env: str, tmp_rel: str, name: str) -> str | None:
    for c in (os.environ.get(env), str(TMP / tmp_rel), shutil.which(name)):
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def kernel_at_least(major: int, minor: int) -> bool:
    try:
        parts = platform.release().split("-")[0].split(".")
        return (int(parts[0]), int("".join(ch for ch in parts[1] if ch.isdigit()) or 0)) >= (major, minor)
    except (IndexError, ValueError):
        return False


def smoke_qwen38flash(r: dict) -> int:
    base = os.environ.get("QWEN38_URL")
    r["note"] = "serving check only; quality vs qwen3.6:35b needs the 48-case decision benchmark"
    if not base:
        r["reason"] = ("set QWEN38_URL to an OpenAI-compatible base already serving a Qwen3.8-Flash-Next GGUF "
                       "(smallest upstream quants are ~66-68 GB: ISTA-DASLab GSQ-RCO Q2_0 / IQ2_XS). The smoke never "
                       "loads a model itself; start llama-server under ~/DEVELOP/pfy-mentat/tmp and respect the "
                       "nimo memory edge (Entries 089-094)")
        return 2
    body = json.dumps({"model": os.environ.get("QWEN38_MODEL", "qwen3.8-flash"), "temperature": 0, "max_tokens": 64,
                       "messages": [{"role": "user", "content": "Reply with exactly this token and nothing else: PFY-OK-095"}]}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        r["reason"] = f"no usable response from {base}: {e}"
        return 2 if isinstance(e, urllib.error.URLError) and not isinstance(e, urllib.error.HTTPError) else 1
    r["seconds"] = round(time.time() - t, 1)
    try:
        text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        r["reason"] = f"unexpected response shape: {str(data)[:400]}"
        return 1
    r["output"] = text[-300:]
    r["usage"] = data.get("usage")
    if "PFY-OK-095" not in text:
        r["reason"] = "model answered but did not return the exact token"
        return 1
    return 0


def smoke_sandlock(r: dict) -> int:
    b = find_bin("SANDLOCK_BIN", "sandlock/sandlock", "sandlock")
    r["bin"], r["kernel"] = b, platform.release()
    if platform.system() != "Linux" or not kernel_at_least(6, 12):
        r["reason"] = f"Sandlock needs Linux 6.12+ (Landlock ABI v6); this host is {platform.system()} {platform.release()}"
        return 2
    if not b:
        r["reason"] = ("no sandlock binary. Operator: unpack the upstream release tarball "
                       "(sandlock-x86_64-unknown-linux-gnu.tar.gz, check its sha256) into ~/DEVELOP/pfy-mentat/tmp/sandlock/ "
                       "-- no root, no cargo install to ~/.cargo")
        return 2
    with tempfile.TemporaryDirectory(prefix="pfy-sandlock-") as d:
        ok, no = Path(d, "ok"), Path(d, "no")
        ok.mkdir(); no.mkdir()
        ro = [x for x in ("/usr", "/lib", "/lib64", "/bin", "/etc") if os.path.exists(x)]
        cmd = [b, "run"] + sum((["-r", x] for x in ro), []) + ["-w", str(ok), "--", "/bin/sh", "-c",
               f"echo allowed > {ok}/a; echo denied > {no}/b; exit 0"]
        try:
            p = run(cmd, timeout=60)
        except subprocess.TimeoutExpired:
            r["reason"] = "sandlock run timed out"
            return 1
        r["output"] = (p.stdout + p.stderr)[-600:]
        allowed, leaked = (ok / "a").exists(), (no / "b").exists()
        r["allowed_write_landed"], r["denied_write_leaked"] = allowed, leaked
        if leaked:
            r["reason"] = "write outside the granted dir succeeded: confinement not enforced"
            return 1
        if not allowed:
            r["reason"] = f"granted write did not land (rc={p.returncode})"
            return 1
    return 0


def smoke_foremerge(r: dict) -> int:
    b = find_bin("FOREMERGE_BIN", "foremerge/foremerge", "foremerge")
    r["bin"] = b
    r["note"] = "local ledger in a throwaway repo; no `foremerge setup` (it edits client MCP configs)"
    if not b:
        r["reason"] = ("no foremerge binary. Operator: unpack the upstream release tarball "
                       "(foremerge-v0.5.1-x86_64-unknown-linux-gnu.tar.gz, check its sha256) into "
                       "~/DEVELOP/pfy-mentat/tmp/foremerge/ -- not install.sh (writes ~/.local/bin), no `setup`")
        return 2
    if not shutil.which("git"):
        r["reason"] = "git not on PATH"
        return 2

    def fm(args: list[str], cwd: str) -> dict:
        p = run([b, "--json"] + args, cwd=cwd, timeout=60)
        try:
            return json.loads(p.stdout)
        except ValueError:
            return {"ok": False, "raw": (p.stdout + p.stderr)[-400:], "rc": p.returncode}

    with tempfile.TemporaryDirectory(prefix="pfy-foremerge-") as d:
        g = ["git", "-c", "user.email=smoke@localhost", "-c", "user.name=smoke"]
        run(["git", "init", "-q"], cwd=d)
        run(g + ["commit", "-q", "--allow-empty", "-m", "init"], cwd=d)
        steps = {"init": fm(["init"], d)}
        agent = fm(["agent", "register", "--name", "smoke-a", "--model", "none"], d)
        aid = (agent.get("data") or {}).get("id")
        if not aid:
            r["steps"] = {"init": steps["init"], "agent": agent}
            r["reason"] = "agent register returned no id (CLI shape changed?)"
            return 1
        fm(["intent", "publish", "--agent", aid, "--task", "T1", "--summary",
            "Replace PaymentService with StripePaymentService", "--scope", "symbol:PaymentService=replace"], d)
        clash = fm(["conflicts", "check", "--intent", "Add PayPal support to PaymentService",
                    "--scope", "symbol:PaymentService=extend"], d)
        clean = fm(["conflicts", "check", "--intent", "Edit README", "--scope", "file:README.md=modify"], d)
    hits = [c for c in (clash.get("data") or {}).get("conflicts", []) if c.get("severity") == "HIGH"]
    stray = (clean.get("data") or {}).get("conflicts", [])
    r["high_conflicts"] = [{k: c.get(k) for k in ("kind", "severity", "explanation")} for c in hits]
    r["unrelated_conflicts"] = len(stray) if isinstance(stray, list) else stray
    if not hits:
        r["reason"] = f"expected a HIGH replace-vs-extend conflict, got {str(clash)[:400]}"
        return 1
    if stray:
        r["reason"] = "unrelated scope reported a conflict (false positive)"
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", required=True, choices=["qwen38flash", "sandlock", "foremerge"])
    a = ap.parse_args()
    receipt = {"entry": a.entry, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "host": os.uname().nodename}
    code = {"qwen38flash": smoke_qwen38flash, "sandlock": smoke_sandlock, "foremerge": smoke_foremerge}[a.entry](receipt)
    return write(a.entry, receipt, code)


if __name__ == "__main__":
    sys.exit(main())
