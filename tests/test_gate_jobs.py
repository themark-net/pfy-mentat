"""Behavior of scripts/pfy_gate_jobs.py: Build-job Tester and Reviewer gates.

Fake grok commands stand in for `grok -p`. Each fake reads GATE_SHA,
GATE_BASE, GATE_JOB and GATE_VERDICT from its env and writes (or fails to
write) a verdict. The runner must pin the SHA and fail closed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "pfy_gate_jobs.py"
SCRATCH = ROOT / "tmp" / "gate-jobs-tests"


def git(cwd: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return out.stdout.strip()


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="gj-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        (self.repo / ".gitignore").write_text("tmp/\n")
        (self.repo / "a.py").write_text("a = 1\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "a.py").write_text("a = 2\n")
        git(self.repo, "commit", "-qam", "change")
        self.sha = git(self.repo, "rev-parse", "HEAD")
        self.out = self.tmp / "verdicts"

    def fake(self, body: str) -> str:
        path = self.tmp / "fakegrok.py"
        path.write_text(
            "#!/usr/bin/env python3\nimport os, sys, subprocess, time\nfrom pathlib import Path\n"
            "sha = os.environ['GATE_SHA']; job = os.environ['GATE_JOB']\n"
            "verdict = Path(os.environ['GATE_VERDICT'])\n" + body,
            encoding="utf-8",
        )
        path.chmod(0o755)
        return "%s %s" % (sys.executable, path)

    def run_gate(self, grok_cmd: str, *extra: str, sha: str | None = None, timeout: float = 120) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(RUNNER), "run", "--repo", str(self.repo), "--sha", sha or self.sha,
                "--base", self.base, "--out", str(self.out), "--grok-cmd", grok_cmd, "--timeout", "20", *extra]
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)

    def verdict(self, job: str) -> str:
        return (self.out / self.sha / ("%s.md" % job)).read_text(encoding="utf-8")

    def header(self, job: str) -> dict:
        found = {}
        for line in self.verdict(job).splitlines()[:8]:
            if ": " in line:
                k, v = line.split(": ", 1)
                found[k.strip()] = v.strip()
        return found

    def check(self, sha: str | None = None) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(RUNNER), "check", "--sha", sha or self.sha, "--out", str(self.out)]
        return subprocess.run(argv, capture_output=True, text=True, timeout=60)


GOOD = "verdict.write_text('SHA: %s\\nVERDICT: PASS\\n\\nevidence: ran the suite\\n' % sha)\n"


class BothJobsRunPinned(_Base):
    def test_both_pass_writes_two_pinned_pass_verdicts_and_exits_zero(self) -> None:
        proc = self.run_gate(self.fake(GOOD))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for job in ("tester", "reviewer"):
            h = self.header(job)
            self.assertEqual((h.get("VERDICT"), h.get("SHA"), h.get("JOB"), h.get("REASON")), ("PASS", self.sha, job, "ok"))
            self.assertIn("evidence: ran the suite", self.verdict(job))
        self.assertEqual(self.check().returncode, 0)

    def test_job_runs_in_an_isolated_checkout_of_the_exact_sha(self) -> None:
        (self.repo / "a.py").write_text("dirty = 1\n")  # caller checkout is dirty and must not leak in
        body = (
            "head = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()\n"
            "content = Path('a.py').read_text()\n"
            "ok = head == sha and content == 'a = 2\\n' and Path.cwd().resolve() != Path(%r).resolve()\n"
            "verdict.write_text('SHA: %%s\\nVERDICT: %%s\\n' %% (sha, 'PASS' if ok else 'FAIL'))\n"
        ) % str(self.repo)
        proc = self.run_gate(self.fake(body))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((self.repo / "a.py").read_text(), "dirty = 1\n")

    def test_jobs_get_their_role_prompt_with_sha_and_base(self) -> None:
        body = (
            "prompt = sys.argv[sys.argv.index('-p') + 1]\n"
            "ok = sha in prompt and os.environ['GATE_BASE'] in prompt and job.lower() in prompt.lower()\n"
            "verdict.write_text('SHA: %s\\nVERDICT: %s\\n' % (sha, 'PASS' if ok else 'FAIL'))\n"
        )
        self.assertEqual(self.run_gate(self.fake(body)).returncode, 0)

    def test_short_sha_is_resolved_and_pinned_in_full(self) -> None:
        proc = self.run_gate(self.fake(GOOD), sha=self.sha[:7])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.header("tester").get("SHA"), self.sha)

    def test_worktrees_are_removed_after_the_run(self) -> None:
        self.run_gate(self.fake(GOOD))
        listed = git(self.repo, "worktree", "list", "--porcelain")
        self.assertEqual(listed.count("worktree "), 1, listed)


class FailClosed(_Base):
    def assert_fail(self, proc, reason: str, jobs=("tester", "reviewer")) -> None:
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for job in jobs:
            h = self.header(job)
            self.assertEqual((h.get("VERDICT"), h.get("REASON"), h.get("SHA")), ("FAIL", reason, self.sha), self.verdict(job))
        self.assertNotEqual(self.check().returncode, 0)

    def test_no_verdict_file_is_fail(self) -> None:
        self.assert_fail(self.run_gate(self.fake("print('forgot')\n")), "no-verdict")

    def test_verdict_without_a_verdict_line_is_fail(self) -> None:
        self.assert_fail(self.run_gate(self.fake("verdict.write_text('SHA: %s\\nlooks fine\\n' % sha)\n")), "no-verdict")

    def test_crash_is_fail_even_if_a_pass_was_written(self) -> None:
        self.assert_fail(self.run_gate(self.fake(GOOD + "sys.exit(3)\n")), "crash")

    def test_timeout_is_fail(self) -> None:
        proc = self.run_gate(self.fake(GOOD + "time.sleep(60)\n"), "--timeout", "2")
        self.assert_fail(proc, "timeout")

    def test_verdict_for_a_different_sha_is_rejected(self) -> None:
        body = "verdict.write_text('SHA: %s\\nVERDICT: PASS\\n' % os.environ['GATE_BASE'])\n"
        self.assert_fail(self.run_gate(self.fake(body)), "sha-mismatch")

    def test_job_that_moves_head_is_fail(self) -> None:
        body = "subprocess.run(['git','checkout','-q',os.environ['GATE_BASE']])\n" + GOOD
        self.assert_fail(self.run_gate(self.fake(body)), "sha-moved")

    def test_missing_grok_binary_is_fail(self) -> None:
        self.assert_fail(self.run_gate(str(self.tmp / "no-such-grok")), "crash")

    def test_rerun_that_writes_nothing_does_not_reuse_the_previous_pass(self) -> None:
        self.assertEqual(self.run_gate(self.fake(GOOD)).returncode, 0)
        self.assert_fail(self.run_gate(self.fake("pass\n")), "no-verdict")

    def test_job_output_is_kept_in_a_log_beside_the_verdict(self) -> None:
        self.run_gate(self.fake("print('probe output ' + job)\nsys.exit(3)\n"))
        for job in ("tester", "reviewer"):
            self.assertIn("probe output " + job, (self.out / self.sha / ("%s.log" % job)).read_text())

    def test_one_failing_job_fails_the_gate(self) -> None:
        body = "word = 'FAIL' if job == 'reviewer' else 'PASS'\nverdict.write_text('SHA: %s\\nVERDICT: %s\\n' % (sha, word))\n"
        proc = self.run_gate(self.fake(body))
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.header("tester").get("VERDICT"), "PASS")
        self.assertEqual((self.header("reviewer").get("VERDICT"), self.header("reviewer").get("REASON")), ("FAIL", "ok"))
        self.assertNotEqual(self.check().returncode, 0)

    def test_unknown_sha_fails_without_running_jobs(self) -> None:
        marker = self.tmp / "ran"
        proc = self.run_gate(self.fake("Path(%r).write_text('1')\n" % str(marker) + GOOD), sha="deadbeef" * 5)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(marker.exists())


class CheckRejectsForeignVerdicts(_Base):
    def test_check_rejects_verdicts_pinned_to_another_sha(self) -> None:
        self.assertEqual(self.run_gate(self.fake(GOOD)).returncode, 0)
        for job in ("tester", "reviewer"):
            p = self.out / self.sha / ("%s.md" % job)
            p.write_text(p.read_text().replace("SHA: %s" % self.sha, "SHA: %s" % self.base))
        proc = self.check()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("sha", (proc.stdout + proc.stderr).lower())

    def test_check_with_missing_verdicts_is_fail(self) -> None:
        proc = self.check()
        self.assertNotEqual(proc.returncode, 0)

    def test_check_reports_json_summary(self) -> None:
        self.run_gate(self.fake(GOOD))
        data = json.loads((self.out / self.sha / "summary.json").read_text())
        self.assertEqual(data["sha"], self.sha)
        self.assertEqual(data["verdict"], "PASS")
        self.assertEqual(sorted(data["jobs"]), ["reviewer", "tester"])


if __name__ == "__main__":
    unittest.main()
