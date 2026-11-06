"""Commit recheck keeps real git history and does not retry an environment failure.

How this fails: the recheck checkout is a new one-commit repo, so history
checks that only skip on a shallow clone fail, the runner asks the agent to
fix that, and a docs-only diff still pays for the flake gate.
How we recover: recheck is a detached worktree of the same repo, a missing
cited commit is a skip, the same failure on the base commit stops as
recheck-env-failed with no second agent prompt, and a docs-only diff runs
the suite at most twice after the edit.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_pfy_build_cloud import (
    CLOUD,
    SCRATCH,
    _drop_external_worktrees,
    _git,
    _init_repo,
    _load_cloud,
    _run,
    _worktree_paths,
    _write_exe,
)

ROOT = Path(__file__).resolve().parents[1]
HISTORY_SHAS = ("7197200", "c0d9072")


def _common_dir(repo: Path) -> str:
    proc = _git(repo, "rev-parse", "--git-common-dir")
    raw = (proc.stdout or "").strip()
    if not raw:
        return ""
    path = Path(raw)
    if not path.is_absolute():
        path = repo / path
    return os.path.realpath(path)


def _recheck_left(repo: Path) -> list[str]:
    names = []
    for path in _worktree_paths(repo):
        if "recheck-" in path.name:
            names.append(str(path))
    parent_globs = []
    for path in _worktree_paths(repo):
        parent = path.parent
        if parent.is_dir():
            parent_globs.append(parent)
    seen = set()
    for parent in parent_globs:
        for child in parent.glob("recheck-*"):
            if str(child) not in seen:
                seen.add(str(child))
                names.append(str(child))
    return names


class HistorySkipTests(unittest.TestCase):
    def setUp(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.repo = _init_repo(SCRATCH / self.id().replace(".", "_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_history_checks_skip_when_the_commit_is_missing(self) -> None:
        """Fail: a non-shallow repo without the cited commits still fails the
        history checks. Recover: each check skips when cat-file cannot see
        that commit, and this checkout still runs the check."""
        from tests.git_history import commit_available
        from tests.test_docs_hygiene import skip_reason_for_history
        from tests.test_dogfood2_1031_report import real_tree_skip_reason
        from tests.test_handoff_headless_1105 import landed_commit_skip_reason

        shallow = _git(self.repo, "rev-parse", "--is-shallow-repository")
        self.assertEqual((shallow.stdout or "").strip(), "false", shallow.stderr)
        for sha in HISTORY_SHAS:
            self.assertFalse(commit_available(self.repo, sha), sha)
            self.assertTrue(commit_available(ROOT, sha), sha)

        docs_reason = skip_reason_for_history(self.repo)
        self.assertIsNotNone(docs_reason)
        self.assertIn("7197200", docs_reason or "")
        self.assertIsNone(skip_reason_for_history(ROOT))

        handoff_reason = landed_commit_skip_reason(self.repo)
        self.assertIsNotNone(handoff_reason)
        self.assertIsNone(landed_commit_skip_reason(ROOT))

        dogfood_reason = real_tree_skip_reason(self.repo)
        self.assertIsNotNone(dogfood_reason)
        self.assertIsNone(real_tree_skip_reason(ROOT))


class RecheckWorktreeTests(unittest.TestCase):
    def setUp(self) -> None:
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.repo = _init_repo(SCRATCH / self.id().replace(".", "_"))
        self.side = SCRATCH / (self.id().replace(".", "_") + "-side")
        self.side.mkdir(parents=True, exist_ok=True)
        self.receipt_dir = self.side / "receipt"

    def tearDown(self) -> None:
        _drop_external_worktrees(self.repo)
        shutil.rmtree(self.repo, ignore_errors=True)
        shutil.rmtree(self.side, ignore_errors=True)

    def _assert_recheck_gone(self) -> None:
        left = _recheck_left(self.repo)
        self.assertEqual(left, [], "recheck worktree still registered or on disk: %s" % left)

    def _build(self, grok: Path, gate: Path, task: str, extra: list[str] | None = None, env: dict | None = None):
        argv = [
            sys.executable,
            str(CLOUD),
            task,
            "--repo",
            str(self.repo),
            "--base",
            "HEAD",
            "--timeout",
            "60",
            "--test-cmd",
            "%s %s" % (sys.executable, gate),
            "--grok-cmd",
            str(grok),
            "--receipt-dir",
            str(self.receipt_dir),
        ]
        if extra:
            argv.extend(extra)
        merged = {
            "PFY_SOURCE_ROOT": str(ROOT),
            "PFY_FIXTURE_COMMON": _common_dir(self.repo),
        }
        if env:
            merged.update(env)
        return _run(argv, self.repo, env=merged, timeout=90)

    def _receipt(self) -> dict:
        return json.loads((self.receipt_dir / "receipt.json").read_text(encoding="utf-8"))

    def _install_recheck_hook(self) -> None:
        """A post-checkout hook that fails only for a recheck checkout.

        The build worktree path does not contain recheck-. If the recheck
        copy inherits this hook, worktree add fails and the run cannot pass.
        """
        hooks = self.repo / ".git" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        hook = hooks / "post-checkout"
        hook.write_text(
            "#!/bin/sh\n"
            "top=$(git rev-parse --show-toplevel 2>/dev/null || true)\n"
            'case "$top" in\n'
            "  *recheck-*)\n"
            "    echo hook-inherited\n"
            "    exit 1\n"
            "    ;;\n"
            "esac\n"
            "exit 0\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)

    def test_recheck_passes_for_docs_only_when_history_commits_are_absent(self) -> None:
        """Fail: a docs-only commit is rechecked in a one-commit archive, the
        cited history commits are missing, and the run is commit-recheck-failed.
        Recover: the recheck worktree shares this repo, the missing commits
        are a skip, the docs commit lands, and the recheck dir is gone."""
        self._install_recheck_hook()
        gate = _write_exe(
            self.side / "gate.py",
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, os.environ['PFY_SOURCE_ROOT'])\n"
            "from tests.git_history import commit_available\n"
            "import subprocess\n"
            "root = Path('.').resolve()\n"
            "missing = [sha for sha in ('7197200', 'c0d9072') if not commit_available(root, sha)]\n"
            "if missing != ['7197200', 'c0d9072']:\n"
            "    print('HISTORY-PRESENT %s' % missing)\n"
            "    raise SystemExit(1)\n"
            "shallow = subprocess.run(['git', 'rev-parse', '--is-shallow-repository'], capture_output=True, text=True)\n"
            "if (shallow.stdout or '').strip() == 'true':\n"
            "    print('SHALLOW')\n"
            "    raise SystemExit(1)\n"
            "common = subprocess.run(['git', 'rev-parse', '--git-common-dir'], capture_output=True, text=True)\n"
            "raw = (common.stdout or '').strip()\n"
            "path = Path(raw)\n"
            "if not path.is_absolute():\n"
            "    path = root / path\n"
            "if os.path.realpath(path) != os.path.realpath(os.environ['PFY_FIXTURE_COMMON']):\n"
            "    print('FAIL: test_closed_eval_rows_are_done_with_the_main_sha')\n"
            "    print('FAIL: test_handoff_cites_the_landed_commits')\n"
            "    print('FAIL: test_real_tree_matches_receipts_and_trailers')\n"
            "    print(path)\n"
            "    raise SystemExit(1)\n"
            "print('ok')\n"
            "raise SystemExit(0)\n",
        )
        grok = _write_exe(
            self.side / "grok.py",
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "Path('docs').mkdir(exist_ok=True)\n"
            "Path('docs/note.md').write_text('Recheck keeps the repo history.\\n', encoding='utf-8')\n"
            "raise SystemExit(0)\n",
        )
        proc = self._build(
            grok,
            gate,
            "document the recheck rule",
            extra=["--no-review", "--retries", "0"],
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        self.assertEqual(proc.returncode, 0, text)
        self.assertNotIn("hook-inherited", text)
        payload = self._receipt()
        self.assertEqual(payload["status"], "PASS", payload)
        self.assertEqual(payload["reason"], "ok")
        self.assertIsNotNone(payload["commit"])
        subject = _git(self.repo, "log", "-1", "--format=%s", payload["commit"])
        self.assertNotEqual((subject.stdout or "").strip(), "recheck")
        shown = _git(self.repo, "show", payload["commit"] + ":docs/note.md")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("Recheck keeps the repo history.", shown.stdout)
        parents = _git(self.repo, "rev-list", "--count", payload["commit"])
        self.assertGreaterEqual(int((parents.stdout or "0").strip()), 2, parents.stdout)
        self._assert_recheck_gone()

    def test_base_failure_is_env_error_and_does_not_retry(self) -> None:
        """Fail: the recheck gate fails, the base would fail the same tests,
        and the next prompt asks the agent to fix it.
        Recover: receipt reason recheck-env-failed, one agent call, no branch,
        and no recheck worktree left behind."""
        log = self.side / "prompts.txt"
        gate = _write_exe(
            self.side / "gate.py",
            "#!/usr/bin/env python3\n"
            "import os\n"
            "from pathlib import Path\n"
            "if Path(os.getcwd()).name.startswith('recheck-'):\n"
            "    print('FAIL: test_closed_eval_rows (tests.test_docs_hygiene.DocsHygieneTests.test_closed_eval_rows_are_done_with_the_main_sha)')\n"
            "    print('FAIL: test_handoff_cites (tests.test_handoff_headless_1105.HeadlessHandoffTests.test_handoff_cites_the_landed_commits)')\n"
            "    raise SystemExit(1)\n"
            "print('ok')\n"
            "raise SystemExit(0)\n",
        )
        grok = _write_exe(
            self.side / "grok.py",
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "blob = '\\n'.join(sys.argv)\n"
            "Path(os.environ['PFY_PROMPT_LOG']).open('a', encoding='utf-8').write(blob + '\\n---PROMPT---\\n')\n"
            "if 'PFY-CLOUD-REVIEW' in blob:\n"
            "    print('verdict: accept')\n"
            "    raise SystemExit(0)\n"
            "Path('kept.py').write_text('value = 1\\n', encoding='utf-8')\n"
            "raise SystemExit(0)\n",
        )
        proc = self._build(
            grok,
            gate,
            "add kept value",
            extra=["--retries", "2"],
            env={"PFY_PROMPT_LOG": str(log)},
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        self.assertEqual(proc.returncode, 1, text)
        payload = self._receipt()
        self.assertEqual(payload["reason"], "recheck-env-failed", payload)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(len(payload["attempts"]), 1, payload["attempts"])
        self.assertIsNone(payload["branch"])
        self.assertIsNone(payload["commit"])
        self.assertTrue((payload.get("recovery") or "").strip())
        prompts = log.read_text(encoding="utf-8").split("---PROMPT---")
        implement = [
            item
            for item in prompts
            if "PFY-CLOUD-IMPLEMENT" in item and "PFY-CLOUD-REVIEW" not in item
        ]
        self.assertEqual(len(implement), 1, prompts)
        self.assertNotIn("commit-recheck-failed", implement[0])
        self.assertNotIn("recheck-env-failed", implement[0])
        self._assert_recheck_gone()

    def test_docs_only_diff_runs_the_suite_at_most_twice(self) -> None:
        """Fail: a docs-only edit still runs the post-change gate, the flake
        gate, and the recheck. Recover: after the file exists the suite runs
        twice, the post-change gate and the recheck, and not the flake gate."""
        log = self.side / "gates.txt"
        gate = _write_exe(
            self.side / "gate.py",
            "#!/usr/bin/env python3\n"
            "import os\n"
            "from pathlib import Path\n"
            "flag = 'changed' if Path('docs/note.md').is_file() else 'base'\n"
            "with Path(os.environ['PFY_GATE_LOG']).open('a', encoding='utf-8') as handle:\n"
            "    handle.write(flag + '\\n')\n"
            "print('ok')\n"
            "raise SystemExit(0)\n",
        )
        grok = _write_exe(
            self.side / "grok.py",
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "Path('docs').mkdir(exist_ok=True)\n"
            "Path('docs/note.md').write_text('docs only\\n', encoding='utf-8')\n"
            "raise SystemExit(0)\n",
        )
        proc = self._build(
            grok,
            gate,
            "document the daily command",
            extra=["--no-review", "--retries", "0"],
            env={"PFY_GATE_LOG": str(log)},
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        self.assertEqual(proc.returncode, 0, text)
        rows = [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        changed = [line for line in rows if line == "changed"]
        self.assertEqual(changed, ["changed", "changed"], rows)
        self.assertLessEqual(len(changed), 2, rows)
        self._assert_recheck_gone()

    def test_recheck_checkout_is_private(self) -> None:
        """Fail: worktree add on the short parent follows the umask, so the
        recheck tree is 0775 while the gate runs and other users can read it.
        Recover: the directory is 0700 before the gate, the run passes, and
        the directory is gone afterwards."""
        log = self.side / "mode.txt"
        gate = _write_exe(
            self.side / "gate.py",
            "#!/usr/bin/env python3\n"
            "import os\n"
            "from pathlib import Path\n"
            "here = Path('.').resolve()\n"
            "if here.name.startswith('recheck-'):\n"
            "    mode = here.stat().st_mode & 0o777\n"
            "    with Path(os.environ['PFY_MODE_LOG']).open('a', encoding='utf-8') as handle:\n"
            "        handle.write('%04o\\n' % mode)\n"
            "    if mode != 0o700:\n"
            "        raise SystemExit(1)\n"
            "print('ok')\n"
            "raise SystemExit(0)\n",
        )
        grok = _write_exe(
            self.side / "grok.py",
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "Path('kept.py').write_text('value = 1\\n', encoding='utf-8')\n"
            "raise SystemExit(0)\n",
        )
        proc = self._build(
            grok,
            gate,
            "add a private recheck",
            extra=["--no-review", "--retries", "0"],
            env={"PFY_MODE_LOG": str(log)},
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        self.assertEqual(proc.returncode, 0, text)
        modes = [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(modes, text)
        self.assertTrue(all(line == "0700" for line in modes), modes)
        payload = self._receipt()
        self.assertEqual(payload["status"], "PASS", payload)
        self.assertEqual(payload["reason"], "ok")
        self._assert_recheck_gone()

    def test_recheck_worktree_is_removed_when_the_gate_raises(self) -> None:
        """Fail: an exception during the recheck gate leaves the extra
        worktree registered. Recover: the worktree is removed and pruned,
        and the checkout that did run shared this repo's object store."""
        mod = _load_cloud()
        head = _git(self.repo, "rev-parse", "HEAD").stdout.strip()
        args = mod.parse_args(
            [
                "add a note",
                "--repo",
                str(self.repo),
                "--base",
                "HEAD",
                "--retries",
                "0",
                "--no-review",
                "--timeout",
                "30",
                "--test-cmd",
                "true",
                "--grok-cmd",
                "true",
                "--receipt-dir",
                str(self.receipt_dir),
            ]
        )
        build = mod.CloudBuild(args, self.repo, "HEAD", head, "true")
        try:
            prepared = build.prepare_worktree()
            self.assertIsNone(prepared, build.recovery_detail)
            seen: dict[str, str] = {}
            original = build.gate

            def boom(cwd=None):
                if cwd is not None and "recheck-" in Path(cwd).name:
                    seen["cwd"] = str(cwd)
                    proc = subprocess.run(
                        ["git", "rev-parse", "--git-common-dir"],
                        cwd=cwd,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    raw = (proc.stdout or "").strip()
                    path = Path(raw)
                    if raw and not path.is_absolute():
                        path = Path(cwd) / path
                    seen["common"] = os.path.realpath(path) if raw else ""
                    raise RuntimeError("gate exploded")
                return original(cwd)

            build.gate = boom
            with self.assertRaises(RuntimeError):
                build.recheck_sha(head)
            self.assertEqual(seen.get("common"), _common_dir(self.repo), seen)
            self.assertFalse(Path(seen["cwd"]).exists(), seen)
            self._assert_recheck_gone()
        finally:
            build.drop_worktree()


if __name__ == "__main__":
    unittest.main()
