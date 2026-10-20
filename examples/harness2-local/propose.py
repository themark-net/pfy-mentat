#!/usr/bin/env python3
"""Push a harness proposal branch, or write a negative finding.

Host-side only. The diff is the mapped harness. The receipt is the item 6
held-out result. This script never merges, never force-pushes, and never
updates main, master, stage, dev, or build/*.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "examples" / "x-intake-local"))

import cases  # noqa: E402
import leaks  # noqa: E402
import smoke  # noqa: E402

# One line on purpose. Lowering it to 1 lets a +1 gain push.
GAIN_MIN = 2
# One switch. True blocks everyday option words and the false-positive test goes red.
BLOCK_BARE_LABELS = False

_GIT = [
    "git",
    "-c",
    "user.email=harness2-local@example.com",
    "-c",
    "user.name=harness2-local",
]
_TEMP_OK = re.compile(r"temperature:\s*0(?:\.0+)?(?![\d.])")
_SEED_OK = re.compile(r"seed:\s*230(?!\d)")
_PROTECTED = {"main", "master", "stage", "dev"}


def secret_pattern() -> re.Pattern[str]:
    """Token shapes. Not bare substrings such as ``sk-`` or ``xai-``."""
    return re.compile(
        r"(?<![A-Za-z0-9])("
        r"gh[pousr]_[A-Za-z0-9]{36,}|"
        r"github_pat_[A-Za-z0-9_]{60,}|"
        r"xai-[A-Za-z0-9]{40,}|"
        r"sk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}|"
        r"AKIA[0-9A-Z]{16}|"
        r"AIza[0-9A-Za-z_-]{35}|"
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
        r")"
    )


def _mask(secret: str) -> str:
    return secret[:4] + "***"


def scan_secrets(text: str, env: dict[str, str]) -> list[str]:
    """Masked prefixes of token hits and of PAID_KEYS values found in the diff."""
    found: list[str] = []
    for match in secret_pattern().finditer(text):
        found.append(_mask(match.group(1)))
    for name in smoke.PAID_KEYS:
        value = env.get(name) or ""
        # Shorter than 8 matches ordinary words. Compared, never printed.
        if len(value) < 8 or value not in text:
            continue
        found.append(_mask(value))
    out: list[str] = []
    for item in found:
        if item not in out:
            out.append(item)
    return out


def _line_leaks(text: str, real_ids: list[str], labels: list[str], notes: list[str]) -> bool:
    if leaks.real_id_hits(text, real_ids):
        return True
    if leaks.pair_hits(text, real_ids, labels):
        return True
    if leaks.short_id_hits(text):
        return True
    if leaks.note_hits(text, notes):
        return True
    if leaks.verdict_hits(text, labels):
        return True
    if BLOCK_BARE_LABELS and leaks.bare_label_hits(text, labels):
        return True
    return False


def added_lines(diff: str) -> list[tuple[int, str]]:
    """1-based diff line numbers and the added text. ``+++`` headers are skipped."""
    rows = []
    for lineno, raw in enumerate(diff.splitlines(), 1):
        if raw.startswith("+++"):
            continue
        if raw.startswith("+"):
            rows.append((lineno, raw[1:]))
    return rows


def leak_blocks(
    rows: list[tuple[int, str]],
    real_ids: list[str],
    labels: list[str],
    notes: list[str],
) -> list[int]:
    return [lineno for lineno, text in rows if _line_leaks(text, real_ids, labels, notes)]


def leak_warnings(
    rows: list[tuple[int, str]],
    labels: list[str],
    blocked: set[int],
) -> list[tuple[int, str]]:
    warns = []
    for lineno, text in rows:
        if lineno in blocked:
            continue
        if leaks.bare_label_hits(text, labels) or leaks.verdict_near_letter(text):
            warns.append((lineno, text))
    return warns


def name_is_protected(branch: str) -> bool:
    name = branch.strip()
    if name in _PROTECTED:
        return True
    return name.startswith("build/")


def _count(block: dict, *keys: str) -> float:
    for key in keys:
        if key in block:
            return block[key]
    raise KeyError(keys[0])


def _run(block: dict) -> dict:
    return {
        "correct": int(_count(block, "correct", "n_correct")),
        "n": int(block["n"]),
        "wbc": int(block["wrong_but_confident"]),
        "parse_ok": float(block["parse_ok"]),
        "install_mode": block.get("install_mode"),
    }


def _better(a1: dict, a2: dict) -> dict:
    if a1["correct"] != a2["correct"]:
        return a1 if a1["correct"] > a2["correct"] else a2
    return a1 if a1["wbc"] <= a2["wbc"] else a2


def _post_lines(log: str) -> list[str]:
    return [line for line in log.splitlines() if line.startswith("POST ")]


def gate_finding(receipt: dict) -> str | None:
    """None when the held-out gate passes. Otherwise the negative-finding name."""
    held = receipt.get("heldout") or {}
    try:
        a1 = _run(held["a1"])
        a2 = _run(held["a2"])
        final = _run(held["c"])
    except (KeyError, TypeError, ValueError):
        return "gain"
    modes = [receipt.get("install_mode"), a1["install_mode"], a2["install_mode"], final["install_mode"]]
    modes = [mode for mode in modes if mode]
    if not modes or any(mode != "workspace_config" for mode in modes):
        return "install_mode"
    if any(row["n"] != 16 for row in (a1, a2, final)):
        return "gain"
    better = _better(a1, a2)
    gain = final["correct"] - better["correct"]
    gap = abs(a1["correct"] - a2["correct"])
    if gain < GAIN_MIN or (gap >= 2 and gain <= gap):
        return "gain"
    if final["wbc"] > better["wbc"]:
        return "wrong-but-confident"
    if final["parse_ok"] < better["parse_ok"]:
        return "parse_ok"
    posts = _post_lines(str(receipt.get("relay_log") or ""))
    if not posts or any(_TEMP_OK.search(line) is None for line in posts):
        return "temperature"
    if any(_SEED_OK.search(line) is None for line in posts):
        return "seed"
    return None


def _write_receipt(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git_env(work: Path) -> dict[str, str]:
    empty = work / "empty-gitconfig"
    if not empty.exists():
        empty.write_text("", encoding="utf-8")
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = str(empty)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_AUTHOR_NAME"] = "harness2-local"
    env["GIT_AUTHOR_EMAIL"] = "harness2-local@example.com"
    env["GIT_COMMITTER_NAME"] = "harness2-local"
    env["GIT_COMMITTER_EMAIL"] = "harness2-local@example.com"
    return env


def _run_git(args: list[str], *, cwd: Path | None, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_GIT, *args],
        cwd=None if cwd is None else str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def _ref_exists(remote: str, name: str, env: dict[str, str]) -> bool:
    proc = _run_git(["ls-remote", "--heads", remote, name], cwd=None, env=env)
    return bool(proc.stdout.strip())


def _free_name(remote: str, name: str, env: dict[str, str]) -> str:
    if not _ref_exists(remote, name, env):
        return name
    n = 2
    while _ref_exists(remote, f"{name}-{n}", env):
        n += 1
    return f"{name}-{n}"


def _commit_body(receipt: dict, warns: list[tuple[int, str]]) -> str:
    held = receipt["heldout"]
    a1 = _run(held["a1"])
    a2 = _run(held["a2"])
    final = _run(held["c"])
    lines = [
        "harness2-local: proposal",
        "",
        f"before: a1 {a1['correct']}/{a1['n']}, a2 {a2['correct']}/{a2['n']}",
        f"after: {final['correct']}/{final['n']}",
        f"wrong-but-confident: {a1['wbc']},{a2['wbc']} -> {final['wbc']}",
        f"parse_ok: {a1['parse_ok']},{a2['parse_ok']} -> {final['parse_ok']}",
    ]
    if warns:
        lines.append("")
        lines.append("Leak warnings:")
        for lineno, text in warns:
            lines.append(f"{lineno}: {text}")
    return "\n".join(lines) + "\n"


def _publish(
    *,
    remote: str,
    work: Path,
    diff: str,
    branch: str,
    date: str,
    receipt: dict,
    warns: list[tuple[int, str]],
) -> tuple[int, str]:
    work.mkdir(parents=True, exist_ok=True)
    env = _git_env(work)
    if branch and name_is_protected(branch):
        print(f"BLOCKED: protected branch {branch.strip()}")
        return 2, ""
    clone = _run_git(["clone", "--branch", "main", remote, str(work / "tree")], cwd=None, env=env)
    if clone.returncode != 0:
        work.mkdir(parents=True, exist_ok=True)
        print("BLOCKED: remote unreachable")
        return 2, ""
    tree = work / "tree"
    diff_path = work / "proposal.diff"
    diff_path.write_text(diff if diff.endswith("\n") else diff + "\n", encoding="utf-8")
    applied = _run_git(["apply", "--whitespace=nowarn", str(diff_path)], cwd=tree, env=env)
    if applied.returncode != 0:
        print("BLOCKED: diff did not apply")
        return 2, ""
    added = _run_git(["add", "--all"], cwd=tree, env=env)
    if added.returncode != 0:
        print("BLOCKED: git add failed")
        return 2, ""
    msg_path = work / "commit-msg.txt"
    msg_path.write_text(_commit_body(receipt, warns), encoding="utf-8")
    committed = _run_git(["commit", "-F", str(msg_path)], cwd=tree, env=env)
    if committed.returncode != 0:
        print("BLOCKED: git commit failed")
        return 2, ""
    if not branch:
        short = _run_git(["rev-parse", "--short=12", "HEAD"], cwd=tree, env=env)
        if short.returncode != 0 or not short.stdout.strip():
            print("BLOCKED: no commit sha")
            return 2, ""
        branch = f"bot/h2-proposal-{date}-{short.stdout.strip()}"
    if name_is_protected(branch):
        print(f"BLOCKED: protected branch {branch.strip()}")
        return 2, ""
    branch = _free_name(remote, branch, env)
    pushed = _run_git(["push", remote, f"HEAD:refs/heads/{branch}"], cwd=tree, env=env)
    if pushed.returncode != 0:
        print("BLOCKED: push failed")
        return 2, ""
    print(f"pushed {branch}")
    return 0, branch


def _bank() -> tuple[list[str], list[str], list[str]]:
    bank = cases.load_bank()
    ids = cases.case_ids(bank)
    labels = sorted({case["label"] for case in bank["cases"]})
    notes = [case.get("note") or "" for case in bank["cases"]]
    return ids, labels, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Propose a harness branch or record a negative finding.")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--diff", required=True)
    parser.add_argument("--remote", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--branch", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--date", default="")
    args = parser.parse_args(argv)

    diff = Path(args.diff).read_text(encoding="utf-8")
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else (REPO / "tmp" / "host-only" / "proposal-receipt.json")
    date = args.date or datetime.date.today().strftime("%Y%m%d")
    real_ids, labels, notes = _bank()
    rows = added_lines(diff)

    secrets = scan_secrets(diff, dict(os.environ))
    if secrets:
        for prefix in secrets:
            print(f"BLOCKED: secret {prefix}")
        return 2

    blocked = leak_blocks(rows, real_ids, labels, notes)
    if blocked:
        _write_receipt(
            out,
            {"item": 5, "lines": blocked, "negative_finding": "label-leak", "status": "DONE"},
        )
        print("negative_finding: label-leak")
        return 0

    finding = gate_finding(receipt)
    if finding:
        _write_receipt(out, {"item": 5, "negative_finding": finding, "status": "DONE"})
        print(f"negative_finding: {finding}")
        return 0

    warns = leak_warnings(rows, labels, set())
    code, pushed = _publish(
        remote=args.remote,
        work=Path(args.work_dir),
        diff=diff,
        branch=args.branch,
        date=date,
        receipt=receipt,
        warns=warns,
    )
    if code == 0:
        _write_receipt(
            out,
            {"branch": pushed, "item": 5, "negative_finding": None, "status": "DONE"},
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
