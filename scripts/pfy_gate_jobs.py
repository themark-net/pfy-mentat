#!/usr/bin/env python3
"""Pin a commit and run the Tester and Reviewer gate jobs. Fail closed.

`run` checks out the requested SHA in a detached worktree per job, runs a
headless Grok Build command, and writes the verdict files itself.
`check` reads those files. Bots call `check` and do not parse the jobs.

Exit codes:
  run:   0 both jobs PASS, 1 a job failed, 2 unknown SHA or bad arguments
  check: 0 both verdicts pass for that SHA, 1 otherwise
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

JOBS = ("tester", "reviewer")
# The tester hit 40 turns on the 533a634 replay before writing a verdict.
DEFAULT_TURNS = {"tester": 80, "reviewer": 40}
# One blank line is the header separator. Three more keep a raw VERDICT or
# SHA line outside the first eight lines of the file.
_RAW_PAD = "\n\n\n\n"
_GIT_LOCK = threading.Lock()


class ResolveError(Exception):
    def __init__(self, rev: str, detail: str) -> None:
        super().__init__(detail)
        self.rev = rev
        self.detail = detail


def _is_full_sha(value: str) -> bool:
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _git(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def resolve_commit(repo: Path, rev: str) -> str:
    proc = _git(repo, ["rev-parse", "--verify", f"{rev}^{{commit}}"])
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "not a commit").strip()
        raise ResolveError(rev, detail)
    sha = proc.stdout.strip()
    if not _is_full_sha(sha):
        raise ResolveError(rev, f"resolved to {sha!r}")
    return sha


def _head(wt: Path) -> str | None:
    if not wt.exists():
        return None
    proc = _git(wt, ["rev-parse", "HEAD"])
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def _add_worktree(repo: Path, wt: Path, sha: str) -> subprocess.CompletedProcess[str]:
    with _GIT_LOCK:
        wt.parent.mkdir(parents=True, exist_ok=True)
        return _git(repo, ["worktree", "add", "--detach", str(wt), sha])


def _remove_worktree(repo: Path, wt: Path) -> None:
    with _GIT_LOCK:
        _git(repo, ["worktree", "remove", "--force", str(wt)])
        _git(repo, ["worktree", "prune"])


def render_prompt(job: str, sha: str, base: str, verdict: str, brief: str) -> str:
    path = Path(__file__).resolve().parent / "gate_prompts" / f"{job}.md"
    text = path.read_text(encoding="utf-8")
    for key, val in (
        ("{sha}", sha),
        ("{base}", base),
        ("{job}", job),
        ("{verdict}", verdict),
        ("{brief}", brief),
    ):
        text = text.replace(key, val)
    return text


def _kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except OSError:
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def run_grok(
    argv: list[str], cwd: Path, env: dict[str, str], timeout: float, log: Path
) -> tuple[bool, bool, int | None]:
    """Return (started, timed_out, exit_code). Job stdout and stderr go to log."""
    with open(log, "ab") as sink:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as exc:
            sink.write(f"could not start {argv[0]}: {exc}\n".encode())
            return False, False, None
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        return True, True, proc.returncode
    return True, False, code


def judge(
    *,
    timed_out: bool,
    crashed: bool,
    head: str | None,
    sha: str,
    raw: str | None,
) -> tuple[str, str]:
    """Return (VERDICT, REASON). Check order is the fail-closed order."""
    if timed_out:
        return "FAIL", "timeout"
    if crashed:
        return "FAIL", "crash"
    if head != sha:
        return "FAIL", "sha-moved"
    if raw is None:
        return "FAIL", "no-verdict"
    lines = raw.splitlines()
    word = None
    for line in lines:
        if line in ("VERDICT: PASS", "VERDICT: FAIL"):
            word = line.split(": ", 1)[1]
            break
    if word is None:
        return "FAIL", "no-verdict"
    want = f"SHA: {sha}"
    named = [line for line in lines if line.startswith("SHA:")]
    if want not in lines or any(line != want for line in named):
        return "FAIL", "sha-mismatch"
    return word, "ok"


def render_final(verdict: str, sha: str, job: str, reason: str, raw: str | None) -> str:
    text = (
        f"VERDICT: {verdict}\n"
        f"SHA: {sha}\n"
        f"JOB: {job}\n"
        f"REASON: {reason}\n"
        f"{_RAW_PAD}"
    )
    if raw:
        text += raw if raw.endswith("\n") else raw + "\n"
    return text


def run_job(
    *,
    repo: Path,
    sha: str,
    base: str,
    job: str,
    out: Path,
    grok_cmd: str,
    timeout: float,
    max_turns: int,
    brief: str,
    keep: bool,
) -> dict:
    t0 = time.monotonic()
    raw_path = (out / sha / f"{job}.raw.md").resolve()
    final_path = out / sha / f"{job}.md"
    log_path = out / sha / f"{job}.log"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    # A re-run must never judge or publish the previous run's files.
    for stale in (raw_path, final_path, log_path):
        stale.unlink(missing_ok=True)
    wt = (repo / "tmp" / "gate-jobs" / f"{sha[:12]}-{job}-{os.getpid()}").resolve()
    timed_out = False
    crashed = False
    head: str | None = None
    try:
        add = _add_worktree(repo, wt, sha)
        if add.returncode != 0:
            crashed = True
        else:
            head = _head(wt)
            if head == sha:
                (wt / "tmp").mkdir(parents=True, exist_ok=True)
                try:
                    prompt = render_prompt(job, sha, base, str(raw_path), brief)
                except OSError:
                    crashed = True
                else:
                    argv = shlex.split(grok_cmd) + ["-p", prompt, "--max-turns", str(max_turns)]
                    env = os.environ.copy()
                    env["GATE_SHA"] = sha
                    env["GATE_BASE"] = base
                    env["GATE_JOB"] = job
                    env["GATE_VERDICT"] = str(raw_path)
                    env["TMPDIR"] = str((wt / "tmp").resolve())
                    started, timed_out, exit_code = run_grok(argv, wt, env, timeout, log_path)
                    head = _head(wt)
                    if not timed_out and (not started or exit_code != 0):
                        crashed = True
    except Exception:
        if not timed_out:
            crashed = True
    finally:
        if not keep:
            _remove_worktree(repo, wt)
    raw = raw_path.read_text(encoding="utf-8", errors="replace") if raw_path.is_file() else None
    verdict, reason = judge(timed_out=timed_out, crashed=crashed, head=head, sha=sha, raw=raw)
    final_path.write_text(render_final(verdict, sha, job, reason, raw), encoding="utf-8")
    return {
        "verdict": verdict,
        "reason": reason,
        "seconds": round(time.monotonic() - t0, 3),
    }


def _out_dir(out: str | None, repo: Path | None) -> Path:
    if out:
        return Path(out)
    if repo is not None:
        return repo / "tmp" / "gate-verdicts"
    return Path.cwd() / "tmp" / "gate-verdicts"


def cmd_run(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    try:
        sha = resolve_commit(repo, args.sha)
    except ResolveError as exc:
        print(f"error: unknown commit {exc.rev}: {exc.detail}", file=sys.stderr)
        return 2
    try:
        base = resolve_commit(repo, args.base)
    except ResolveError as exc:
        print(f"error: unknown base {exc.rev}: {exc.detail}", file=sys.stderr)
        return 2
    if args.brief:
        brief_path = Path(args.brief)
        if not brief_path.is_file():
            print(f"error: brief file not found: {brief_path}", file=sys.stderr)
            return 2
        brief = brief_path.read_text(encoding="utf-8")
    else:
        brief = "(none)"
    jobs = tuple(j for j in JOBS if j in args.jobs.split(","))
    if not jobs or set(args.jobs.split(",")) - set(JOBS):
        print(f"error: --jobs must name {','.join(JOBS)}", file=sys.stderr)
        return 2
    out = _out_dir(args.out, repo)
    (out / sha).mkdir(parents=True, exist_ok=True)
    (out / sha / "summary.json").unlink(missing_ok=True)
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {
            pool.submit(
                run_job,
                repo=repo,
                sha=sha,
                base=base,
                job=job,
                out=out,
                grok_cmd=args.grok_cmd,
                timeout=args.timeout,
                max_turns=args.max_turns or DEFAULT_TURNS[job],
                brief=brief,
                keep=args.keep,
            ): job
            for job in jobs
        }
        for fut, job in futures.items():
            results[job] = fut.result()
    ordered = {job: results[job] for job in jobs}
    passed = all(ordered[job]["verdict"] == "PASS" and ordered[job]["reason"] == "ok" for job in jobs)
    summary = {
        "sha": sha,
        "base": base,
        "verdict": "PASS" if passed else "FAIL",
        "jobs": ordered,
    }
    (out / sha / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for job in jobs:
        rec = ordered[job]
        print(f"{job}: {rec['verdict']} {rec['reason']}", file=sys.stderr)
    return 0 if passed else 1


def _parse_header(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        if line == "":
            break
        if ": " in line:
            key, val = line.split(": ", 1)
            found[key.strip()] = val.strip()
    return found


def _sha_ok(requested: str, header_sha: str) -> bool:
    if header_sha == requested:
        return True
    return bool(requested) and len(requested) < len(header_sha) and header_sha.startswith(requested)


def _locate(out: Path, requested: str, repo: Path | None) -> tuple[Path | None, str | None]:
    """Return (verdict dir, error). Error is set when the SHA is ambiguous."""
    if repo is not None and repo.is_dir():
        try:
            full = resolve_commit(repo, requested)
        except ResolveError:
            full = None
        if full and (out / full).is_dir():
            return out / full, None
    direct = out / requested
    if direct.is_dir():
        return direct, None
    if not out.is_dir():
        return None, None
    matches = [
        path
        for path in out.iterdir()
        if path.is_dir() and _is_full_sha(path.name) and path.name.startswith(requested)
    ]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"sha {requested} matches more than one verdict directory"
    return None, None


def cmd_check(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve() if args.repo else None
    out = _out_dir(args.out, repo)
    directory, error = _locate(out, args.sha, repo)
    if error:
        print(error)
        return 1
    problems: list[str] = []
    for job in JOBS:
        path = (directory / f"{job}.md") if directory is not None else None
        if path is None or not path.is_file():
            problems.append(f"{job}: missing verdict file")
            continue
        header = _parse_header(path.read_text(encoding="utf-8", errors="replace"))
        verdict = header.get("VERDICT", "")
        reason = header.get("REASON", "")
        header_sha = header.get("SHA", "")
        if verdict != "PASS":
            problems.append(f"{job}: verdict {verdict or 'missing'}")
        elif reason != "ok":
            problems.append(f"{job}: reason {reason or 'missing'}")
        elif not _sha_ok(args.sha, header_sha):
            problems.append(
                f"{job}: sha mismatch (header sha {header_sha or 'missing'}, requested sha {args.sha})"
            )
    if problems:
        print("\n".join(problems))
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfy_gate_jobs")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run tester and reviewer against a pinned SHA")
    run.add_argument("--repo", required=True)
    run.add_argument("--sha", required=True)
    run.add_argument("--base", required=True)
    run.add_argument("--out", default=None)
    run.add_argument("--grok-cmd", default="grok")
    run.add_argument("--timeout", type=float, default=1800)
    run.add_argument("--max-turns", type=int, default=None, help="default: tester 80, reviewer 40")
    run.add_argument("--jobs", default="tester,reviewer", help="comma list; check still needs both")
    run.add_argument("--brief", default=None)
    run.add_argument("--keep", action="store_true")

    check = sub.add_parser("check", help="accept only two PASS/ok verdicts for this SHA")
    check.add_argument("--sha", required=True)
    check.add_argument("--out", default=None)
    check.add_argument("--repo", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "check":
        return cmd_check(args)
    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
