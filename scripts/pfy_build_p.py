#!/usr/bin/env python3
"""pfy build -p: jev toolset (local) + decision shadow + grok -p (plain).

Dogfood D1 friction fix: wrap headless Grok Build so bots use --output-format plain (never text) and do not skip decision smoke.

Exit codes:
  0  READY (dry-run complete, or grok finished)
  1  FAIL (grok missing / unauthenticated / apply/smoke/grok hard fail)
  2  usage
  3  reserved (decision escalate is logged; build still proceeds unless
     PFY_BUILD_ABORT_ON_ESCALATE=1)

Receipt: <cwd>/pipelines/dogfood/build/<timestamp>/receipt.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def _now():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _append_receipt(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(row)
    row.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _encode_cwd(cwd: Path) -> str:
    # grok sessions dir uses percent-encoded absolute path
    return urllib.parse.quote(str(cwd.resolve()), safe="")


def find_latest_session(cwd: Path, grok_home: Path | None = None) -> str | None:
    home = Path(grok_home or os.environ.get("GROK_HOME") or (Path.home() / ".grok"))
    sess_root = home / "sessions" / _encode_cwd(cwd)
    if not sess_root.is_dir():
        return None
    newest = None
    newest_mtime = -1.0
    for child in sess_root.iterdir():
        if not child.is_dir():
            continue
        usage = child / "usage.json"
        m = usage.stat().st_mtime if usage.is_file() else child.stat().st_mtime
        if m > newest_mtime:
            newest_mtime = m
            newest = child.name
    return newest


def read_usage(cwd: Path, session_id: str, grok_home: Path | None = None) -> dict:
    home = Path(grok_home or os.environ.get("GROK_HOME") or (Path.home() / ".grok"))
    usage_path = home / "sessions" / _encode_cwd(cwd) / session_id / "usage.json"
    if not usage_path.is_file():
        return {}
    try:
        return json.loads(usage_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def grok_bin(path_env: str | None = None) -> str | None:
    return shutil.which("grok", path=path_env if path_env is not None else os.environ.get("PATH"))


def grok_authenticated(grok_home: Path | None = None) -> bool:
    home = Path(grok_home or os.environ.get("GROK_HOME") or (Path.home() / ".grok"))
    auth = home / "auth.json"
    try:
        return auth.is_file() and auth.stat().st_size > 20
    except OSError:
        return False


def run_cmd(argv: list[str], *, cwd: Path, env: dict | None = None, dry_run: bool = False) -> dict:
    if dry_run:
        return {"ok": True, "dry_run": True, "argv": argv, "rc": 0, "stdout": "", "stderr": ""}
    proc = subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )
    return {
        "ok": proc.returncode == 0,
        "rc": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "argv": argv,
    }


def apply_jev_local(repo: Path, *, dry_run: bool, env: dict) -> dict:
    argv = [str(repo / "pfy"), "toolset", "apply", "jev", "--harness", "grok", "--lane", "local"]
    if not dry_run:
        argv.append("--yes")
    return run_cmd(argv, cwd=repo, env=env, dry_run=dry_run)


def decision_smoke(repo: Path, *, dry_run: bool, env: dict) -> dict:
    argv = [str(repo / "pfy"), "decision", "smoke"]
    return run_cmd(argv, cwd=repo, env=env, dry_run=dry_run)


def decision_route_shadow(repo: Path, *, dry_run: bool, env: dict) -> dict:
    """Run route; escalate (rc 3) is a valid shadow verdict — not a build abort."""
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "rc": 3,
            "verdict": "escalate",
            "stdout": "ESCALATE decision · (dry-run shadow)\n  verdict: escalate\n",
            "stderr": "",
            "argv": [str(repo / "pfy"), "decision", "route"],
        }
    argv = [str(repo / "pfy"), "decision", "route"]
    proc = subprocess.run(argv, cwd=str(repo), env=env, text=True, capture_output=True)
    out = proc.stdout or ""
    verdict = "ready"
    if proc.returncode == 3 or "verdict: escalate" in out or out.startswith("ESCALATE"):
        verdict = "escalate"
    elif proc.returncode != 0:
        verdict = "fail"
    return {
        "ok": proc.returncode in (0, 3),
        "rc": proc.returncode,
        "verdict": verdict,
        "stdout": out,
        "stderr": proc.stderr or "",
        "argv": argv,
    }


def run_grok_p(
    *,
    prompt: str,
    cwd: Path,
    grok: str,
    dry_run: bool,
    env: dict,
) -> dict:
    argv = [
        grok,
        "-p",
        prompt,
        "--cwd",
        str(cwd),
        "--always-approve",
        "--output-format",
        "plain",
    ]
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "rc": 0,
            "argv": argv,
            "stdout": "(dry-run: grok not executed)",
            "stderr": "",
            "session_id": None,
            "usage": {},
        }
    before = time.time()
    proc = subprocess.run(argv, cwd=str(cwd), env=env, text=True, capture_output=True)
    session_id = find_latest_session(cwd)
    usage = read_usage(cwd, session_id) if session_id else {}
    return {
        "ok": proc.returncode == 0,
        "rc": proc.returncode,
        "argv": argv,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "elapsed_s": round(time.time() - before, 3),
        "session_id": session_id,
        "usage": usage,
    }


def build_p(
    prompt: str,
    *,
    cwd: Path | None = None,
    repo: Path | None = None,
    dry_run: bool = False,
    path_env: str | None = None,
    grok_home: Path | None = None,
    abort_on_escalate: bool | None = None,
) -> int:
    repo = Path(repo or ROOT).resolve()
    cwd = Path(cwd or repo).resolve()
    stamp = _now()
    receipt_dir = cwd / "pipelines" / "dogfood" / "build" / stamp
    receipt = receipt_dir / "receipt.jsonl"
    env = os.environ.copy()
    env.setdefault("PFY_DECISION_PATH", "cua-s1-forms")
    env.setdefault("PFY_JEV_OFFLINE", "1")
    env.pop("TYPESAFE_API_KEY", None)
    if grok_home is not None:
        env["GROK_HOME"] = str(grok_home)

    if abort_on_escalate is None:
        abort_on_escalate = os.environ.get("PFY_BUILD_ABORT_ON_ESCALATE", "").strip() in (
            "1",
            "true",
            "yes",
        )

    _append_receipt(
        receipt,
        {
            "event": "start",
            "prompt_head": prompt[:240],
            "cwd": str(cwd),
            "repo": str(repo),
            "dry_run": dry_run,
            "typesafe_tokens": 0,
        },
    )

    grok = grok_bin(path_env)
    if not grok:
        msg = "FAIL: grok not on PATH — install Grok Build CLI or fix PATH; next: ~/.local/bin/grok"
        print(msg, file=sys.stderr)
        _append_receipt(receipt, {"event": "fail", "reason": "grok_missing", "copy": msg})
        return EXIT_FAIL
    if not grok_authenticated(Path(env["GROK_HOME"]) if "GROK_HOME" in env else grok_home):
        # In dry-run allow missing auth so CI can exercise the path
        if not dry_run:
            msg = (
                "FAIL: grok unauthenticated — missing/empty ~/.grok/auth.json "
                "(or $GROK_HOME/auth.json); next: run `grok` once to log in"
            )
            print(msg, file=sys.stderr)
            _append_receipt(receipt, {"event": "fail", "reason": "grok_unauthenticated", "copy": msg})
            return EXIT_FAIL

    print("pfy build -p · toolset apply jev --lane local%s" % (" · dry-run" if dry_run else ""))
    apply = apply_jev_local(repo, dry_run=dry_run, env=env)
    _append_receipt(receipt, {"event": "toolset_apply", **{k: apply[k] for k in apply if k != "stdout"}})
    if not apply.get("ok") and not dry_run:
        print(apply.get("stderr") or apply.get("stdout") or "FAIL toolset apply", file=sys.stderr)
        _append_receipt(receipt, {"event": "fail", "reason": "toolset_apply", "rc": apply.get("rc")})
        return EXIT_FAIL
    if apply.get("stdout"):
        print(apply["stdout"].rstrip())

    print("pfy build -p · decision smoke")
    smoke = decision_smoke(repo, dry_run=dry_run, env=env)
    _append_receipt(
        receipt,
        {
            "event": "decision_smoke",
            "rc": smoke.get("rc"),
            "ok": smoke.get("ok"),
            "stdout_head": (smoke.get("stdout") or "")[:500],
        },
    )
    if not smoke.get("ok") and not dry_run:
        print(smoke.get("stderr") or smoke.get("stdout") or "FAIL decision smoke", file=sys.stderr)
        _append_receipt(receipt, {"event": "fail", "reason": "decision_smoke", "rc": smoke.get("rc")})
        return EXIT_FAIL
    if smoke.get("stdout"):
        print(smoke["stdout"].rstrip())

    print("pfy build -p · decision route (shadow)")
    route = decision_route_shadow(repo, dry_run=dry_run, env=env)
    _append_receipt(
        receipt,
        {
            "event": "decision_route_shadow",
            "rc": route.get("rc"),
            "verdict": route.get("verdict"),
            "ok": route.get("ok"),
            "stdout_head": (route.get("stdout") or "")[:500],
            "note": "escalate is valid; no silent auto-act",
        },
    )
    if route.get("stdout"):
        print(route["stdout"].rstrip())
    if route.get("verdict") == "fail" and not dry_run:
        print("FAIL: decision route broken (not escalate)", file=sys.stderr)
        _append_receipt(receipt, {"event": "fail", "reason": "decision_route_broken", "rc": route.get("rc")})
        return EXIT_FAIL
    if route.get("verdict") == "escalate" and abort_on_escalate and not dry_run:
        print("FAIL: PFY_BUILD_ABORT_ON_ESCALATE=1 and route escalated", file=sys.stderr)
        _append_receipt(receipt, {"event": "fail", "reason": "abort_on_escalate"})
        return EXIT_FAIL

    print("pfy build -p · grok -p --output-format plain --always-approve")
    grok_rec = run_grok_p(prompt=prompt, cwd=cwd, grok=grok, dry_run=dry_run, env=env)
    # Persist grok streams for operators
    (receipt_dir / "grok-stdout.log").write_text(grok_rec.get("stdout") or "", encoding="utf-8")
    (receipt_dir / "grok-stderr.log").write_text(grok_rec.get("stderr") or "", encoding="utf-8")
    usage = grok_rec.get("usage") or {}
    sess = usage.get("session") or {}
    summary = {
        "event": "grok_p",
        "rc": grok_rec.get("rc"),
        "ok": grok_rec.get("ok"),
        "dry_run": dry_run,
        "session_id": grok_rec.get("session_id"),
        "elapsed_s": grok_rec.get("elapsed_s"),
        "turnCount": sess.get("turnCount"),
        "modelCalls": sess.get("modelCalls"),
        "totalTokens": sess.get("totalTokens"),
        "primaryModelId": sess.get("primaryModelId"),
        "typesafe_tokens": 0,
        "argv": grok_rec.get("argv"),
    }
    _append_receipt(receipt, summary)

    sid = grok_rec.get("session_id") or "(none)"
    print("session_id: %s" % sid)
    print(
        "usage: turns=%s model_calls=%s total_tokens=%s model=%s"
        % (
            sess.get("turnCount", "(n/a)" if dry_run else "?"),
            sess.get("modelCalls", "(n/a)" if dry_run else "?"),
            sess.get("totalTokens", "(n/a)" if dry_run else "?"),
            sess.get("primaryModelId", "(n/a)" if dry_run else "?"),
        )
    )
    print("receipt: %s" % receipt)

    if not grok_rec.get("ok") and not dry_run:
        err = (grok_rec.get("stderr") or grok_rec.get("stdout") or "").strip()
        print(err or "FAIL: grok -p exited non-zero", file=sys.stderr)
        _append_receipt(receipt, {"event": "fail", "reason": "grok_p", "rc": grok_rec.get("rc")})
        return EXIT_FAIL

    _append_receipt(receipt, {"event": "done", "ok": True, "dry_run": dry_run, "typesafe_tokens": 0})
    print("READY pfy build -p%s" % (" · dry-run" if dry_run else ""))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="pfy build",
        description="Apply local jev toolset, shadow decision, run grok -p (plain).",
    )
    p.add_argument("-p", "--prompt", dest="prompt", help="single-turn prompt for grok -p")
    p.add_argument("--prompt-file", help="read prompt from file")
    p.add_argument("--cwd", help="worktree / working directory for grok and receipt")
    p.add_argument("--dry-run", action="store_true", help="plan + shadow only; do not write toolset or exec grok")
    p.add_argument("--path-env", default=None, help=argparse.SUPPRESS)  # tests: override PATH for which()
    args = p.parse_args(argv)

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    if not prompt or not str(prompt).strip():
        p.print_help()
        print("\nFAIL: need -p \"<prompt>\" or --prompt-file", file=sys.stderr)
        return EXIT_USAGE

    return build_p(
        str(prompt),
        cwd=Path(args.cwd).resolve() if args.cwd else None,
        dry_run=bool(args.dry_run),
        path_env=args.path_env,
    )


if __name__ == "__main__":
    sys.exit(main())
