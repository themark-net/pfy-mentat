"""A full worktree pregate misses tests that need git history.

Fail: tests/test_docs_hygiene.py on 1f3b1a3 runs git cat-file on 7197200.
A depth-1 clone has no that object, so the test exits non-zero. The same
file on 2a74482 sees a shallow repository and returns before the probe, so
the depth-1 run exits 0. A full nimo worktree still has 7197200, so pregate
there stays green.
Recovery: keep the shallow return, or stop probing objects a depth-1
checkout does not have. A new test that runs git cat-file or git show on a
hard-coded old SHA must do the same check.

G0 uses actions/checkout at depth 1. A depth-1 checkout of this branch does
not contain 1f3b1a3 or 2a74482, so the pin proof skips there. The synthetic
repo below still fails an unguarded probe.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = "1f3b1a31cee91df49d39534ff4c8e516544cd596"
GOOD = "2a744823e05588e8d6331d511e2ec7fb77ec0ecb"
OLD_SHA_PROBE = re.compile(
    r"""cat-file|git\s+show\s+[0-9a-f]{7,40}|["']show["']\s*,\s*["'][0-9a-f]{7,40}"""
)


def _scratch() -> Path:
    raw = os.environ.get("TMPDIR") or ""
    path = Path(raw) if raw else ROOT / "tmp"
    resolved = path.resolve()
    if resolved == Path("/tmp") or str(resolved).startswith("/tmp/"):
        path = ROOT / "tmp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _git_ok(args: list[str], cwd: Path | None = None) -> bool:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _have_commit(sha: str) -> bool:
    return _git_ok(["cat-file", "-e", f"{sha}^{{commit}}"])


def _clone_supports_revision() -> bool:
    proc = subprocess.run(
        ["git", "clone", "-h"],
        capture_output=True,
        text=True,
    )
    help_text = proc.stdout + proc.stderr
    # Short help prints "--[no-]revision", which does not contain "--revision".
    return "revision" in help_text


def _depth1_docs_hygiene(sha: str, dest: Path) -> subprocess.CompletedProcess[str]:
    if dest.exists():
        shutil.rmtree(dest)
    src = "file://" + str(ROOT)
    clone = subprocess.run(
        [
            "git",
            "-c",
            "advice.detachedHead=false",
            "clone",
            "--depth=1",
            f"--revision={sha}",
            src,
            str(dest),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if clone.returncode != 0:
        raise AssertionError(f"clone {sha} failed\n{clone.stderr}")
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if shallow.stdout.strip() != "true":
        raise AssertionError(f"clone of {sha} is not shallow: {shallow.stdout!r}")
    return subprocess.run(
        ["python3", "-m", "unittest", "tests.test_docs_hygiene"],
        cwd=dest,
        capture_output=True,
        text=True,
        timeout=120,
    )


class ShallowCheckoutHistoryTests(unittest.TestCase):
    def test_depth1_is_red_on_1f3b1a3_and_green_on_2a74482(self):
        if not _clone_supports_revision():
            self.skipTest("git clone has no --revision")
        missing = [sha for sha in (BAD, GOOD) if not _have_commit(sha)]
        if missing:
            self.skipTest("depth-1 checkout has no " + ", ".join(missing))
        scratch = _scratch() / "shallow-pin-proof"
        scratch.mkdir(parents=True, exist_ok=True)
        try:
            bad = _depth1_docs_hygiene(BAD, scratch / "bad")
            good = _depth1_docs_hygiene(GOOD, scratch / "good")
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        bad_out = bad.stdout + bad.stderr
        self.assertNotEqual(bad.returncode, 0, bad_out)
        self.assertIn("7197200", bad_out)
        self.assertIn("invalid object name", bad_out)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)

    def test_unguarded_old_sha_probe_fails_in_a_depth1_clone(self):
        """Without the shallow return, cat-file of the parent commit fails.

        The passing side of this pair is the real docs-hygiene test on
        2a74482, in the pin test above. This one only shows the missing
        object. It does not reimplement the guard.
        """
        if not _clone_supports_revision():
            self.skipTest("git clone has no --revision")
        scratch = _scratch() / "shallow-synth"
        if scratch.exists():
            shutil.rmtree(scratch)
        origin = scratch / "origin"
        origin.mkdir(parents=True)
        try:
            def git(*args: str) -> str:
                proc = subprocess.run(
                    ["git", *args],
                    cwd=origin,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                return proc.stdout.strip()

            git("init")
            git("config", "user.email", "shallow-proof@example.com")
            git("config", "user.name", "shallow-proof")
            (origin / "f.txt").write_text("one\n", encoding="utf-8")
            git("add", "f.txt")
            git("commit", "-m", "one")
            old = git("rev-parse", "HEAD")
            (origin / "f.txt").write_text("two\n", encoding="utf-8")
            git("commit", "-am", "two")
            tip = git("rev-parse", "HEAD")
            dest = scratch / "shallow"
            clone = subprocess.run(
                [
                    "git",
                    "-c",
                    "advice.detachedHead=false",
                    "clone",
                    "--depth=1",
                    f"--revision={tip}",
                    "file://" + str(origin),
                    str(dest),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(clone.returncode, 0, clone.stderr)
            shallow = subprocess.run(
                ["git", "rev-parse", "--is-shallow-repository"],
                cwd=dest,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            ).stdout.strip()
            self.assertEqual(shallow, "true")
            unguarded = subprocess.run(
                ["git", "cat-file", "-e", f"{old}:f.txt"],
                cwd=dest,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(unguarded.returncode, 0, unguarded.stderr)
            self.assertIn("f.txt", unguarded.stderr + unguarded.stdout)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def test_current_tests_guard_hard_coded_old_sha_probes(self):
        offenders = []
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if path.name == "test_shallow_checkout_history.py":
                continue
            text = path.read_text(encoding="utf-8")
            if not OLD_SHA_PROBE.search(text):
                continue
            if "--is-shallow-repository" not in text:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
