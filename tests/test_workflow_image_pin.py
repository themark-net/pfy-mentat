#!/usr/bin/env python3
"""Behavior of the workflow image-pin lint: real helper, real pregate call.

Fixture files live in tests/fixtures/workflow_image_pin/. Parse cases skip
when this interpreter cannot import yaml, because the helper itself exits 1
in that case and G0's setup-python does not ship PyYAML. The missing-import
case always runs.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "check_workflow_image_pin.py"
FIX = ROOT / "tests" / "fixtures" / "workflow_image_pin"
SCRATCH = ROOT / "tmp"
_RUN_ID_DIR = re.compile(r"^[0-9a-f]{7}-[0-9]{8}T[0-9]{6}Z-[0-9]+$")


def shared_runs_root() -> Path:
    """Runs root pregate uses when PREGATE_RUNS_DIR is unset.

    Same rule as scripts/pregate.sh: the parent of the absolute git common
    dir, then tmp/pregate-runs. From a linked worktree that is the main
    checkout, so a fixture must not persist or prune there.
    """
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return Path(proc.stdout.strip()).parent / "tmp" / "pregate-runs"


def run_dir_names(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {path.name for path in root.iterdir() if path.is_dir()}


def fresh_run_names(root: Path, started: float) -> set[str]:
    """Child directory names whose mtime does not predate `started`."""
    if not root.is_dir():
        return set()
    found: set[str] = set()
    for path in root.iterdir():
        if path.is_dir() and path.stat().st_mtime >= started:
            found.add(path.name)
    return found

try:
    import yaml  # noqa: F401

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

needs_yaml = unittest.skipUnless(
    HAS_YAML,
    "SKIP: PyYAML is not importable; the helper fails closed and these fixtures are not parsed here",
)


def run_helper(*args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["TMPDIR"] = str(SCRATCH)
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        cwd=ROOT,
        env=merged,
        capture_output=True,
        text=True,
        timeout=60,
    )


class WorkflowImagePinTests(unittest.TestCase):
    def assert_pass(self, proc: subprocess.CompletedProcess[str]) -> None:
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertIn("PASS workflow image pin:", proc.stdout)

    def assert_fail(self, proc: subprocess.CompletedProcess[str], needle: str) -> None:
        blob = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, blob)
        self.assertIn(needle, blob)

    def pregate_call_env(self, runs_dir: str | None = None, **extra: str) -> dict[str, str]:
        """Point one pregate call at a temp dir under this worktree.

        Both TMPDIR and PREGATE_RUNS_DIR are set. Pass runs_dir to force a
        bad override (empty, relative, or whitespace) while TMPDIR stays put.
        """
        SCRATCH.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="pregate-fixture-", dir=SCRATCH))
        self.addCleanup(lambda path=work: shutil.rmtree(path, ignore_errors=True))
        env = os.environ.copy()
        env["TMPDIR"] = str(work)
        env["PREGATE_RUNS_DIR"] = str(work) if runs_dir is None else runs_dir
        env.setdefault("PREGATE_MAX_ROOT_LEN", "200")
        env.update(extra)
        return env

    def run_pregate_lint(self, env: dict[str, str], timeout: int = 240) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "nice",
                "-n",
                "19",
                "scripts/pregate.sh",
                "--in-place",
                "--allow-dirty",
                "--only",
                "lint",
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def assert_summary_under(self, proc: subprocess.CompletedProcess[str], runs: Path) -> Path:
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertIn("OVERALL=PASS", proc.stdout)
        match = re.search(r"Summary: (\S+)", proc.stdout)
        self.assertIsNotNone(match, blob)
        summary = Path(match.group(1))
        self.assertEqual(summary.parent.parent, runs, str(summary))
        self.assertRegex(summary.parent.name, _RUN_ID_DIR)
        self.assertTrue(summary.is_file(), summary)
        log = summary.parent / "logs" / "lint.log"
        self.assertIn("PASS workflow image pin:", log.read_text(encoding="utf-8"))
        return summary

    @needs_yaml
    def test_pinned_passes(self) -> None:
        self.assert_pass(run_helper(str(FIX / "pinned.yml")))

    @needs_yaml
    def test_ubuntu_latest_fails(self) -> None:
        self.assert_fail(run_helper(str(FIX / "latest.yml")), "ubuntu-latest")

    @needs_yaml
    def test_list_containing_ubuntu_latest_fails(self) -> None:
        self.assert_fail(run_helper(str(FIX / "list-latest.yml")), "ubuntu-latest")

    @needs_yaml
    def test_matrix_expression_resolving_to_ubuntu_latest_fails(self) -> None:
        self.assert_fail(run_helper(str(FIX / "matrix-latest.yml")), "ubuntu-latest")

    @needs_yaml
    def test_self_hosted_passes(self) -> None:
        self.assert_pass(run_helper(str(FIX / "self-hosted.yml")))

    @needs_yaml
    def test_malformed_yaml_fails_closed(self) -> None:
        proc = run_helper(str(FIX / "malformed.yml"))
        blob = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, blob)
        self.assertIn("malformed YAML", blob)

    @needs_yaml
    def test_pinned_matrix_expression_passes(self) -> None:
        # A resolver that rejects every ${{ }} would fail this file.
        self.assert_pass(run_helper(str(FIX / "pinned-matrix.yml")))

    @needs_yaml
    def test_unpinned_github_image_fails(self) -> None:
        proc = run_helper(str(FIX / "unpinned-image.yml"))
        blob = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, blob)
        self.assertIn("ubuntu-22.04", blob)
        self.assertIn("windows-latest", blob)

    @needs_yaml
    def test_unresolved_expression_fails_closed(self) -> None:
        self.assert_fail(run_helper(str(FIX / "unresolved.yml")), "unresolved")

    @needs_yaml
    def test_reusable_workflow_without_runs_on_passes(self) -> None:
        self.assert_pass(run_helper(str(FIX / "reusable.yml")))

    @needs_yaml
    def test_missing_runs_on_fails_closed(self) -> None:
        self.assert_fail(run_helper(str(FIX / "no-runs-on.yml")), "no runs-on")

    @needs_yaml
    def test_real_workflows_pass(self) -> None:
        self.assert_pass(run_helper(str(ROOT / ".github" / "workflows")))

    @needs_yaml
    def test_empty_directory_fails_closed(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        empty = Path(tempfile.mkdtemp(prefix="image-pin-empty-", dir=SCRATCH))
        try:
            self.assert_fail(run_helper(str(empty)), "no workflow files")
        finally:
            shutil.rmtree(empty)

    def test_missing_pyyaml_fails_closed(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        shadow = Path(tempfile.mkdtemp(prefix="image-pin-nopyyaml-", dir=SCRATCH))
        try:
            (shadow / "yaml.py").write_text("raise ImportError('shadowed')\n", encoding="utf-8")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(shadow) + os.pathsep + env.get("PYTHONPATH", "")
            proc = run_helper(str(FIX / "pinned.yml"), env=env)
            blob = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, blob)
            self.assertIn("PyYAML is not importable", blob)
        finally:
            shutil.rmtree(shadow)

    @needs_yaml
    def test_pregate_lint_calls_helper(self) -> None:
        # --only lint is filemode, launchers, payload lint, catalog_check, and
        # this helper. It does not discover tests. The summary is read from
        # this call's PREGATE_RUNS_DIR. A new folder in the shared runs root
        # (mtime during the call) means the override was ignored.
        shared = shared_runs_root()
        before = run_dir_names(shared)
        started = time.time() - 1.0
        env = self.pregate_call_env()
        runs = Path(env["PREGATE_RUNS_DIR"])
        proc = self.run_pregate_lint(env)
        blob = proc.stdout + proc.stderr
        appeared = fresh_run_names(shared, started) - before
        self.assertEqual(appeared, set(), blob)
        self.assert_summary_under(proc, runs)

    @needs_yaml
    def test_planted_shared_run_survives_keep_one(self) -> None:
        """Keep-1 must not delete a run folder in the shared root.

        The planted id is older than the fixture run. If retention still
        targets the main checkout, keep-1 removes it. Recovery is pruning
        only inside PREGATE_RUNS_DIR.
        """
        shared = shared_runs_root()
        shared.mkdir(parents=True, exist_ok=True)
        before = run_dir_names(shared)
        started = time.time() - 1.0
        planted = shared / f"deadbee-20200101T000000Z-{os.getpid()}"
        planted.mkdir()
        self.addCleanup(lambda path=planted: shutil.rmtree(path, ignore_errors=True))
        marker = planted / "keep.txt"
        marker.write_text("planted\n", encoding="utf-8")
        # write_text updates the directory mtime. Stamp both after that so
        # keep-1 would drop this folder if retention still targeted shared.
        old = time.time() - 86400 * 30
        os.utime(marker, (old, old))
        os.utime(planted, (old, old))
        env = self.pregate_call_env(PREGATE_KEEP_RUNS="1")
        runs = Path(env["PREGATE_RUNS_DIR"])
        proc = self.run_pregate_lint(env)
        blob = proc.stdout + proc.stderr
        self.assertTrue(marker.is_file(), blob)
        self.assertEqual(before - run_dir_names(shared), set(), blob)
        self.assertEqual(fresh_run_names(shared, started) - before, set(), blob)
        self.assert_summary_under(proc, runs)
        kept = [path for path in runs.iterdir() if path.is_dir()]
        self.assertEqual(len(kept), 1, kept)

    def test_bad_runs_dir_exits_2_and_writes_nothing(self) -> None:
        """Empty, relative, or whitespace PREGATE_RUNS_DIR exits 2.

        A script that ignores the override runs lint and writes a shared
        run folder. Recovery is refusing before any persist or prune.
        """
        shared = shared_runs_root()
        pgs = shared.parent / "pgs"
        pg = shared.parent / "pg"
        cases = (
            ("empty", ""),
            ("relative", "relative-pregate-runs"),
            ("whitespace", str(SCRATCH / "bad runs")),
        )
        for label, value in cases:
            with self.subTest(label=label):
                before = run_dir_names(shared)
                before_pgs = run_dir_names(pgs)
                before_pg = run_dir_names(pg)
                started = time.time() - 1.0
                env = self.pregate_call_env(runs_dir=value)
                work = Path(env["TMPDIR"])
                stray: Path | None
                if label == "relative":
                    stray = ROOT / value
                elif label == "whitespace":
                    stray = Path(value)
                else:
                    stray = None
                if stray is not None:
                    self.addCleanup(lambda path=stray: shutil.rmtree(path, ignore_errors=True))
                proc = self.run_pregate_lint(env)
                blob = proc.stdout + proc.stderr
                self.assertEqual(proc.returncode, 2, blob)
                self.assertIn("PREGATE_RUNS_DIR", proc.stderr, blob)
                self.assertNotIn("Summary:", proc.stdout, blob)
                self.assertNotIn("OVERALL=", proc.stdout, blob)
                self.assertEqual(run_dir_names(shared), before, blob)
                self.assertEqual(fresh_run_names(shared, started) - before, set(), blob)
                self.assertEqual(run_dir_names(pgs), before_pgs, blob)
                self.assertEqual(run_dir_names(pg), before_pg, blob)
                self.assertEqual(list(work.iterdir()), [], blob)
                if stray is not None:
                    self.assertFalse(stray.exists(), blob)


if __name__ == "__main__":
    unittest.main()
