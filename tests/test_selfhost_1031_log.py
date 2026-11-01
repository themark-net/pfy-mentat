"""Built-by trailers on this branch must point at a PASS receipt.

A matching subject is either the old hard cut at 72 characters or the
current runner subject (whole words, then an ellipsis). Thirteen selfhost2
cherry-picks amended the subject after the cloud commit. Those shas are
listed. Any other subject fails. A planted trailer in a temp repo fails
when the receipt is missing, not PASS, or the subject does not match.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAILER_PREFIX = "Built-by: ./pfy build (cloud) receipt "


def expected_subject(task: str) -> str:
    """Older runner subject: collapsed task, cut at 72, trailing space removed.

    git stores the subject without a trailing space when the cut lands on
    the space between words. The comparison uses that stored subject.
    """
    collapsed = " ".join((task or "").split())
    return (collapsed[:72] or "task").rstrip()


def runner_subject(task: str) -> str:
    """Current cloud runner subject. Kept in scripts/pfy_build_cloud.py."""
    import importlib.util

    cached = getattr(runner_subject, "fn", None)
    if cached is None:
        path = ROOT / "scripts" / "pfy_build_cloud.py"
        spec = importlib.util.spec_from_file_location("pfy_build_cloud_subject", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load commit_subject")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cached = mod.commit_subject
        setattr(runner_subject, "fn", cached)
    return cached(task)


# Selfhost2 cherry-picks. The cloud subject stayed on the throwaway commit.
# The landed subject was amended. Receipt path is part of the exception so a
# trailer that moves to a different PASS receipt still fails.
AMENDED_CHERRY_PICKS = {
    "18ed977ff5603bc093e7ffeb2f8062a7f972c813": (
        "Skip backup_once when the path is a symlink.",
        "eval/selfhost2-1031/13-backup-once/receipt.json",
    ),
    "c97d0a1fabfc1cd478ec87dae85813d3b3948427": (
        "Treat a symlinked mcp config as absent.",
        "eval/selfhost2-1031/12-apply-mcp/receipt.json",
    ),
    "b6e387a9b6ef8d7c97d399d80a0ee3c9511dd0fe": (
        "Skip the follow when a setup ledger path is a symlink.",
        "eval/selfhost2-1031/11-setup-ledger/receipt.json",
    ),
    "3eeab428e8798577e0d1e0ea1695641490c10c44": (
        "Replace a hedge ledger symlink instead of writing through it.",
        "eval/selfhost2-1031/10-hedge-ledger/receipt.json",
    ),
    "d217349f1acc2df28501d5456a25d92bf0c6264e": (
        "Copy skill symlinks instead of their targets.",
        "eval/selfhost2-1031/09-install-symlink/receipt.json",
    ),
    "67e3333a76c3eae4fc641eea73992cd326d05aae": (
        "Reject a harness symlink without reading its target.",
        "eval/selfhost2-1031/08-surface-symlink/receipt.json",
    ),
    "e6339ca3c6deaa66c80614c204ffa119238e3f65": (
        "Leave a symlinked adapter file in place.",
        "eval/selfhost2-1031/07-adapter-symlink-ops/receipt.json",
    ),
    "1faa9fd7e80beb442b184206e409d07f508b72b6": (
        "Hash smoke 137 fixture symlinks as readlink text.",
        "eval/selfhost2-1031/06-smoke137-hash/receipt.json",
    ),
    "91386568b3c5ad2f22bdfa7d066af1ec76922494": (
        "Hash smoke 140 fixture symlinks as readlink text.",
        "eval/selfhost2-1031/05-smoke140-hash/receipt.json",
    ),
    "ae5e5e5e74597a7eba996bf5e0b47417878a888a": (
        "Hash adapter symlink targets as readlink text.",
        "eval/selfhost2-1031/04-adapter-hash/receipt.json",
    ),
    "36bc071c3e82a8f26cb8494833c078689e3c8f86": (
        "Refuse a relative typed-decisions smoke receipt directory.",
        "eval/selfhost2-1031/03-typed-receipt/receipt.json",
    ),
    "cdf4d681c19c16937a866b2b99d6884a0e7372f4": (
        "Refuse a relative Kolibri smoke receipt directory.",
        "eval/selfhost2-1031/02b-kolibri-receipt/receipt.json",
    ),
    "4a0fe4eeebd2d0d83520e932b4c62eddcad89197": (
        "Record mode and symlink targets in the AgentDescent home snapshot.",
        "eval/selfhost2-1031/01-ad-snap/receipt.json",
    ),
}


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def built_by_problems(repo: Path) -> list[str]:
    """Empty means every Built-by commit on HEAD points at a matching PASS receipt."""
    listed = _git(repo, ["log", "--format=%H", "--grep", TRAILER_PREFIX])
    if listed.returncode != 0:
        return ["git log failed: %s" % (listed.stderr or "").strip()]
    problems: list[str] = []
    for sha in (listed.stdout or "").split():
        shown = _git(repo, ["log", "-1", "--format=%B", sha])
        message = shown.stdout or ""
        rel = ""
        for line in message.splitlines():
            if line.startswith(TRAILER_PREFIX):
                rel = line[len(TRAILER_PREFIX) :].strip()
                break
        if not rel or rel.startswith("/") or ".." in Path(rel).parts:
            problems.append("%s trailer path is missing or unsafe" % sha[:12])
            continue
        path = repo / rel
        if not path.is_file():
            problems.append("%s receipt missing: %s" % (sha[:12], rel))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append("%s receipt unreadable: %s" % (sha[:12], exc))
            continue
        if data.get("status") != "PASS":
            problems.append("%s receipt status is %s" % (sha[:12], data.get("status")))
            continue
        subject = message.splitlines()[0].strip() if message.splitlines() else ""
        task = str(data.get("task") or "")
        if subject == expected_subject(task) or subject == runner_subject(task):
            continue
        if AMENDED_CHERRY_PICKS.get(sha) == (subject, rel):
            continue
        problems.append(
            "%s subject %r != runner subject %r or hard cut %r"
            % (sha[:12], subject, runner_subject(task), expected_subject(task))
        )
    return problems


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    _git(path, ["config", "user.email", "selfhost-test@example.com"])
    _git(path, ["config", "user.name", "selfhost-test"])


def _commit(repo: Path, message: str) -> None:
    (repo / "keep.txt").write_text("ok\n", encoding="utf-8")
    _git(repo, ["add", "keep.txt"])
    proc = _git(repo, ["commit", "-q", "-m", message])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)


class SelfhostBuiltByTests(unittest.TestCase):
    def test_this_branch_has_no_bad_built_by_trailer(self) -> None:
        problems = built_by_problems(ROOT)
        self.assertEqual(problems, [], "\n".join(problems))

    def test_planted_bad_trailer_fails_and_a_pass_receipt_matches(self) -> None:
        scratch = ROOT / "tmp" / "selfhost-1031-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="built-by-", dir=scratch) as td:
            repo = Path(td)
            _init_repo(repo)
            rel = "eval/selfhost-1031/bad/receipt.json"
            receipt = repo / rel
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                json.dumps({"status": "FAIL", "task": "Refuse a relative receipt dir"}) + "\n",
                encoding="utf-8",
            )
            _git(repo, ["add", rel])
            bad = "Refuse a relative receipt dir\n\n%s%s\n" % (TRAILER_PREFIX, rel)
            proc = _git(repo, ["commit", "-q", "-m", bad])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            problems = built_by_problems(repo)
            self.assertTrue(any("status" in item for item in problems), problems)

            receipt.write_text(
                json.dumps({"status": "PASS", "task": "Refuse a relative receipt dir now"}) + "\n",
                encoding="utf-8",
            )
            mismatch = "Some other subject\n\n%s%s\n" % (TRAILER_PREFIX, rel)
            _commit_message_only = _git(repo, ["commit", "-q", "--allow-empty", "-m", mismatch])
            self.assertEqual(_commit_message_only.returncode, 0, _commit_message_only.stderr)
            problems = built_by_problems(repo)
            self.assertTrue(any("subject" in item for item in problems), problems)

            good_task = "Refuse a relative receipt dir now"
            good = "%s\n\n%s%s\n" % (expected_subject(good_task), TRAILER_PREFIX, rel)
            # Replace history of the bad commits with one good commit so the
            # checker sees only the matching PASS trailer.
            shutil.rmtree(repo / ".git")
            _init_repo(repo)
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps({"status": "PASS", "task": good_task}) + "\n",
                encoding="utf-8",
            )
            _git(repo, ["add", rel])
            proc = _git(repo, ["commit", "-q", "-m", good])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(built_by_problems(repo), [])

            os.remove(receipt)
            missing = built_by_problems(repo)
            self.assertTrue(any("missing" in item for item in missing), missing)

    def test_hard_cut_and_ellipsis_pass_and_a_third_subject_fails(self) -> None:
        # Fail: only the hard 72 cut is accepted, so a current runner subject
        # is flagged. Fail the other way: any prose subject is accepted.
        # Recover: accept both shipped forms, and reject a third.
        scratch = ROOT / "tmp" / "selfhost-1031-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="built-by-forms-", dir=scratch) as td:
            repo = Path(td)
            _init_repo(repo)
            task = ("alpha " * 20).strip()
            hard = expected_subject(task)
            ellipsis = runner_subject(task)
            self.assertNotEqual(hard, ellipsis)
            self.assertTrue(ellipsis.endswith("..."), ellipsis)
            for name, subject in (("hard", hard), ("ellipsis", ellipsis)):
                rel = "eval/selfhost-1031/%s/receipt.json" % name
                receipt = repo / rel
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(
                    json.dumps({"status": "PASS", "task": task}) + "\n",
                    encoding="utf-8",
                )
                _git(repo, ["add", rel])
                message = "%s\n\n%s%s\n" % (subject, TRAILER_PREFIX, rel)
                proc = _git(repo, ["commit", "-q", "-m", message])
                self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(built_by_problems(repo), [])

            rel = "eval/selfhost-1031/other/receipt.json"
            receipt = repo / rel
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps({"status": "PASS", "task": task}) + "\n",
                encoding="utf-8",
            )
            _git(repo, ["add", rel])
            message = "A hand written subject\n\n%s%s\n" % (TRAILER_PREFIX, rel)
            proc = _git(repo, ["commit", "-q", "-m", message])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            problems = built_by_problems(repo)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("hand written", problems[0])


if __name__ == "__main__":
    unittest.main()
