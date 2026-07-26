#!/usr/bin/env python3
"""T-0091 phase 4b — voice transcript → tool-capable agent (no manual handoff.sh).

Opt-in: VOICE_AUTO_AGENT=1|grok|mock|opencode (default off).

Runs:
  grok --cwd REPO --max-turns N --always-approve --output-format plain \\
       --prompt-file agent-prompt.md

Writes:
  .generated/last-run.json   status running|done|error|skipped
  .generated/last-run.log    raw agent stdout/stderr tail
  .generated/last-reply.txt  assistant text when available
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

EDGE = Path(__file__).resolve().parent
ROOT = EDGE.parents[1]
DEFAULT_OUT = EDGE / ".generated"
LOCK_NAME = "agent-runner.lock"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_out(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_run(out: Path, payload: dict) -> Path:
    path = out / "last-run.json"
    payload = {**payload, "updated": utc_now()}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def read_run(out: Path) -> dict:
    path = out / "last-run.json"
    if not path.is_file():
        return {"status": "none", "message": "no runs yet"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "error", "message": "corrupt last-run.json"}


def auto_mode() -> str:
    """Return off|mock|grok|opencode."""
    raw = (os.environ.get("VOICE_AUTO_AGENT") or "0").strip().lower()
    if raw in ("", "0", "false", "no", "off"):
        return "off"
    if raw in ("1", "true", "yes", "on", "auto", "grok"):
        return "grok"
    if raw in ("mock", "test"):
        return "mock"
    if raw in ("opencode", "worker"):
        return "opencode"
    return "off"


def _lock_path(out: Path) -> Path:
    return out / LOCK_NAME


def acquire_lock(out: Path) -> bool:
    lp = _lock_path(out)
    if lp.is_file():
        try:
            meta = json.loads(lp.read_text(encoding="utf-8"))
            pid = int(meta.get("pid") or 0)
            # stale if process gone
            if pid and Path(f"/proc/{pid}").exists():
                return False
        except Exception:
            pass
    lp.write_text(
        json.dumps({"pid": os.getpid(), "started": utc_now()}) + "\n",
        encoding="utf-8",
    )
    return True


def release_lock(out: Path) -> None:
    try:
        _lock_path(out).unlink(missing_ok=True)
    except TypeError:
        p = _lock_path(out)
        if p.is_file():
            p.unlink()


def build_prompt(prompt_path: Path | None, transcript: str | None, target: str, repo: Path) -> str:
    if prompt_path and prompt_path.is_file():
        base = prompt_path.read_text(encoding="utf-8").strip()
    elif transcript:
        # minimal wrap if only transcript
        base = (
            f"# Voice → agent (T-0091 4b)\n\n"
            f"**Target:** {target}\n**Repo:** `{repo}`\n\n"
            f"## Spoken intent\n\n{transcript.strip()}\n\n"
            f"You have tools. Land changes in the repo. Prefer cheap checks. "
            f"Stop after success or 3 identical failures.\n"
        )
    else:
        raise ValueError("need --prompt-file or --transcript / --text")

    footer = (
        "\n\n---\n"
        "**Auto-runner mode (4b):** You were invoked headlessly from voice STT. "
        "Execute the request with tools. End with a short status summary "
        "(what ran, pass/fail, next step). Do not ask the user to paste commands "
        "unless blocked on a secret.\n"
    )
    return base + footer


def run_mock(prompt: str, out: Path, run_id: str) -> dict:
    reply = (
        f"[mock agent] Would run tool-capable Grok on:\n"
        f"{prompt[:400]}{'…' if len(prompt) > 400 else ''}\n"
        f"VOICE_RUNNER_MOCK_OK"
    )
    time.sleep(0.2)
    (out / "last-reply.txt").write_text(reply + "\n", encoding="utf-8")
    return {
        "status": "done",
        "ok": True,
        "run_id": run_id,
        "mode": "mock",
        "exit_code": 0,
        "reply": reply,
        "reply_preview": reply[:500],
        "command": ["mock"],
        "duration_s": 0.2,
    }


def run_grok(
    prompt: str,
    repo: Path,
    out: Path,
    *,
    max_turns: int,
    timeout_s: int,
    run_id: str,
) -> dict:
    grok = shutil.which("grok")
    if not grok:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": 127,
            "reply": "",
            "error": "grok not on PATH",
            "command": [],
        }

    prompt_file = out / "last-agent-prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    log_path = out / "last-run.log"

    always = os.environ.get("VOICE_AGENT_ALWAYS_APPROVE", "1").strip() not in (
        "0",
        "false",
        "no",
    )
    cmd = [
        grok,
        "--cwd",
        str(repo),
        "--max-turns",
        str(max_turns),
        "--output-format",
        "plain",
        "--prompt-file",
        str(prompt_file),
        "--no-alt-screen",
    ]
    if always:
        cmd.insert(1, "--always-approve")

    # permission mode bypass if supported — keep always-approve as primary
    env = os.environ.copy()
    env.setdefault("CI", "1")  # some CLIs skip TTY flourishes

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
        duration = round(time.time() - t0, 2)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        log_path.write_text(
            f"$ {' '.join(cmd)}\n\n--- stdout ---\n{stdout}\n\n--- stderr ---\n{stderr}\n",
            encoding="utf-8",
        )
        reply = stdout.strip() or stderr.strip()
        # keep last-reply short for phone
        (out / "last-reply.txt").write_text(reply + ("\n" if reply else ""), encoding="utf-8")
        return {
            "status": "done" if proc.returncode == 0 else "error",
            "ok": proc.returncode == 0,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": proc.returncode,
            "reply": reply[-8000:] if len(reply) > 8000 else reply,
            "reply_preview": (reply[:500] + ("…" if len(reply) > 500 else "")),
            "command": cmd,
            "duration_s": duration,
            "log_path": str(log_path),
            "error": None if proc.returncode == 0 else f"grok exit {proc.returncode}",
        }
    except subprocess.TimeoutExpired as e:
        duration = round(time.time() - t0, 2)
        partial = (e.stdout or b"") if isinstance(e.stdout, (bytes, bytearray)) else (e.stdout or "")
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        log_path.write_text(f"TIMEOUT after {timeout_s}s\n{partial}\n", encoding="utf-8")
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": 124,
            "reply": partial[-4000:] if partial else "",
            "error": f"timeout after {timeout_s}s",
            "command": cmd,
            "duration_s": duration,
            "log_path": str(log_path),
        }
    except Exception as e:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "grok",
            "exit_code": 1,
            "reply": "",
            "error": str(e),
            "command": cmd,
        }


def run_opencode(prompt: str, repo: Path, out: Path, run_id: str, timeout_s: int) -> dict:
    oc = shutil.which("opencode")
    if not oc:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "opencode",
            "error": "opencode not on PATH — use target=monitor or install OpenCode",
            "exit_code": 127,
            "reply": "",
        }
    # OpenCode CLI shapes vary; best-effort non-interactive if supported
    prompt_file = out / "last-agent-prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    log_path = out / "last-run.log"
    # Prefer `opencode run` if present
    cmd = [oc, "run", prompt]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        duration = round(time.time() - t0, 2)
        out_txt = (proc.stdout or "") + (proc.stderr or "")
        log_path.write_text(out_txt, encoding="utf-8")
        (out / "last-reply.txt").write_text(out_txt[-8000:], encoding="utf-8")
        return {
            "status": "done" if proc.returncode == 0 else "error",
            "ok": proc.returncode == 0,
            "run_id": run_id,
            "mode": "opencode",
            "exit_code": proc.returncode,
            "reply": out_txt[-8000:],
            "reply_preview": out_txt[:500],
            "command": cmd,
            "duration_s": duration,
            "log_path": str(log_path),
            "error": None if proc.returncode == 0 else f"opencode exit {proc.returncode}",
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "opencode",
            "error": "opencode run failed — CLI may not support headless run",
            "exit_code": 127,
            "reply": "",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "ok": False,
            "run_id": run_id,
            "mode": "opencode",
            "error": f"timeout after {timeout_s}s",
            "exit_code": 124,
            "reply": "",
        }


def run_once(
    *,
    repo: Path,
    out: Path,
    mode: str,
    target: str,
    prompt_path: Path | None,
    transcript: str | None,
    max_turns: int,
    timeout_s: int,
) -> dict:
    out = ensure_out(out)
    run_id = uuid.uuid4().hex[:12]
    if mode == "off":
        write_run(
            out,
            {
                "status": "skipped",
                "ok": True,
                "run_id": run_id,
                "mode": "off",
                "message": "VOICE_AUTO_AGENT off — set VOICE_AUTO_AGENT=1 to run grok",
            },
        )
        return read_run(out)

    if not acquire_lock(out):
        cur = read_run(out)
        return {
            "status": "busy",
            "ok": False,
            "run_id": run_id,
            "mode": mode,
            "message": "another agent run is in progress",
            "current": cur,
        }

    try:
        prompt = build_prompt(prompt_path, transcript, target, repo)
        write_run(
            out,
            {
                "status": "running",
                "ok": False,
                "run_id": run_id,
                "mode": mode,
                "target": target,
                "started": utc_now(),
                "transcript_preview": (transcript or "")[:200],
                "message": f"agent running ({mode})…",
            },
        )
        print(f"==> agent_runner mode={mode} run_id={run_id} target={target}", file=sys.stderr)

        if mode == "mock":
            result = run_mock(prompt, out, run_id)
        elif mode == "opencode" or target == "worker":
            # worker prefers opencode; if mode grok but target worker, still opencode first
            if mode == "grok" and target == "worker":
                result = run_opencode(prompt, repo, out, run_id, timeout_s)
                if result.get("exit_code") == 127:
                    result = run_grok(
                        prompt, repo, out, max_turns=max_turns, timeout_s=timeout_s, run_id=run_id
                    )
            elif mode == "opencode":
                result = run_opencode(prompt, repo, out, run_id, timeout_s)
            else:
                result = run_grok(
                    prompt, repo, out, max_turns=max_turns, timeout_s=timeout_s, run_id=run_id
                )
        else:
            result = run_grok(
                prompt, repo, out, max_turns=max_turns, timeout_s=timeout_s, run_id=run_id
            )

        result["target"] = target
        result["started"] = result.get("started") or utc_now()
        result["finished"] = utc_now()
        write_run(out, result)
        preview = (result.get("reply_preview") or result.get("reply") or "")[:200]
        print(f"==> agent_runner {result.get('status')} exit={result.get('exit_code')}", file=sys.stderr)
        if preview:
            print(f"==> REPLY: {preview!r}", file=sys.stderr)
        return result
    finally:
        release_lock(out)


def spawn_background(**kwargs) -> str:
    """Start run_once in a daemon thread; return run_id placeholder."""
    run_id = uuid.uuid4().hex[:12]
    out = ensure_out(kwargs["out"])
    write_run(
        out,
        {
            "status": "queued",
            "ok": False,
            "run_id": run_id,
            "mode": kwargs.get("mode"),
            "target": kwargs.get("target"),
            "message": "queued for agent runner",
            "started": utc_now(),
        },
    )

    def _job() -> None:
        try:
            run_once(**kwargs)
        except Exception as e:
            write_run(
                out,
                {
                    "status": "error",
                    "ok": False,
                    "run_id": run_id,
                    "error": str(e),
                    "message": str(e),
                },
            )

    threading.Thread(target=_job, name=f"voice-agent-{run_id}", daemon=True).start()
    return run_id


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="T-0091 4b voice → tool-capable agent runner")
    p.add_argument("--repo", type=Path, default=ROOT)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--prompt-file", type=Path, help="agent-prompt.md path")
    p.add_argument("--transcript", "--text", dest="transcript", help="raw transcript text")
    p.add_argument("--target", default="monitor", choices=["monitor", "worker", "raw"])
    p.add_argument(
        "--mode",
        default=None,
        help="off|mock|grok|opencode|auto|1 (1=grok). Default: VOICE_AUTO_AGENT",
    )
    p.add_argument("--max-turns", type=int, default=int(os.environ.get("VOICE_AGENT_MAX_TURNS", "8")))
    p.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("VOICE_AGENT_TIMEOUT", "600")),
        help="seconds",
    )
    p.add_argument("--background", action="store_true", help="return after queueing")
    p.add_argument("--status", action="store_true", help="print last-run.json and exit")
    args = p.parse_args(argv)

    out = ensure_out(args.out_dir)
    if args.status:
        print(json.dumps(read_run(out), indent=2))
        return 0

    mode = args.mode
    if mode is None or mode == "auto":
        mode = auto_mode()
    elif mode in ("1", "true", "yes", "on"):
        mode = "grok"
    elif mode in ("0", "false", "no"):
        mode = "off"

    # CLI bare default: prefer grok if available else mock
    if args.mode is None and mode == "off":
        mode = "grok" if shutil.which("grok") else "mock"

    if mode not in ("off", "mock", "grok", "opencode"):
        print(f"error: unknown mode {mode!r}", file=sys.stderr)
        return 2

    prompt_path = args.prompt_file
    if prompt_path is None:
        cand = out / "agent-prompt.md"
        if cand.is_file():
            prompt_path = cand
    transcript = args.transcript
    if transcript is None:
        tpath = out / "last-transcript.txt"
        if tpath.is_file():
            transcript = tpath.read_text(encoding="utf-8").strip()

    if args.background:
        rid = spawn_background(
            repo=args.repo.resolve(),
            out=out,
            mode=mode,
            target=args.target,
            prompt_path=prompt_path,
            transcript=transcript,
            max_turns=args.max_turns,
            timeout_s=args.timeout,
        )
        print(json.dumps({"queued": True, "run_id": rid, "mode": mode}, indent=2))
        return 0

    result = run_once(
        repo=args.repo.resolve(),
        out=out,
        mode=mode,
        target=args.target,
        prompt_path=prompt_path,
        transcript=transcript,
        max_turns=args.max_turns,
        timeout_s=args.timeout,
    )
    print(json.dumps({k: result.get(k) for k in (
        "status", "ok", "run_id", "mode", "exit_code", "duration_s", "error", "reply_preview"
    ) if k in result or True}, indent=2))
    # print reply preview always
    if result.get("reply"):
        print("--- reply ---", file=sys.stderr)
        print(result["reply"][:2000], file=sys.stderr)
    return 0 if result.get("ok") or result.get("status") in ("skipped", "done") else 1


if __name__ == "__main__":
    raise SystemExit(main())
