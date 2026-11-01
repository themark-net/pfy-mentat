# Handoff: mvp3-fix2-1031

Branch `bot/mvp3-review-retry`. Worktree `~/DEVELOP/pfy-mentat/tmp/mvp3`. The tip is the commit that adds this file. Its parent is `d2521b5`.

Tester FAIL on `6664713` is answered on this branch. No rebase, no amend, no force push, no merge, no PR.

## Item commits

- BX1 `4c7c5f6`: after the gate, digest each reviewed file and fail closed with `gate-modified-reviewed-file` when the bytes changed. No commit and no retry.
- BX2 `90b51f3`: do not follow symlinks in the review diff. A symlink that resolves outside the worktree is out of scope. The link text is what the prompt and receipts show.
- B2 `1c74003`: M10 an error field beside accept does not commit. M17 `--no-review` leaves `review.retries` at 0. M18 the reviewer prompt contains the changed line. Each test failed against its mutant, then the tree was restored.
- S7 `3392e78`: staged names use `--no-renames`. Excludes come before the names so git 2.53 stages a new path. An in-scope rename commits.
- S8 `301f786`: `git status` and numstat use `-z`. The review diff sets `core.quotepath=false`. `src/café.py` is committed and the prompt contains café.
- Docs `d2521b5`: removed the Known gaps section and the old next-step sentence in `docs/ops/HANDOFF-mvp3-review-retry.md`. `cb2f90e` is the no-change gate. Operator guards name `gate-modified-reviewed-file` and an outside symlink.

## Already done before this lane

Reviewer follow-ups 1-10 were already on this branch. See `docs/ops/HANDOFF-mvp3-followups-1031.md`. `PFY_LOCAL_BUILD_TEST_SEAM` and `PFY_LOCAL_BUILD_INJECT_EXTRA_STAGE` were already in `docs/ops/HANDOFF-pfy-local-build-mvp.md`. `test_ignored_helper_is_not_committed` already expects only `commit-recheck-failed`.

## Suite

Command: `TMPDIR=$PWD/tmp flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock python3 -m unittest discover -s tests -t .`

Ran 1007 tests in 728.294s. FAILED (failures=1, skipped=16). Exit 1.

The one failure is `tests.test_local_bench.OutdirPathTests.test_relative_outdir_log_path_safe`. `TMPDIR` is inside this repo, so the helper returns a relative log path. The mvp3-fix-1031 handoff recorded the same environmental failure. This lane does not change that helper. `tests.test_hedge.DetectorTests.test_detector_runs_offline` did not fail in this run.

Targeted before that run: `tests.test_pfy_build_local_review` and `tests.test_pfy_build_local`, 92 tests, OK, 158.563s. A `BrokenPipeError` from the stub HTTP server during kill-during-review is noise. The result is OK.

## Open

No code item is open. Pregate was not run. The operator runs it. The local default stays NO-GO. The review loop code lands on main after Tester and Reviewer PASS.

t4 still needs a local run that writes the sub-step catch. This lane did not run a real model.
