# Handoff: mvp3-s2s5-1031

Lane: Tester should-fix S2 to S5 on the local build loop.
Branch: `bot/mvp3-s2s5-1031`. Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp3-s2s5-1031`.
Base: `16f17d8`. Head: `a12582f`. No merge, no PR, no tag.
Exit: lane empty. Wall cap was 2026-11-01T09:54:01Z. Clock at exit: 2026-11-01T02:29:15Z.

## S table

| Item | Red repro | Fix SHA | Test |
|---|---|---|---|
| S2 wall budget | `test_wall_budget_stops_a_sleeping_retry_loop` failed: unrecognized `--wall-timeout`, exit 2 | `880478a` | same test. Sleep 30s, wall 2s, ends TIMEOUT `wall-timeout` exit 3 in under 12s, before the retry cap |
| S3 crash label | same module, crash every attempt: receipt reason was `no-change` | `3636a2c` | `test_agent_crash_every_attempt_is_not_labelled_no_change` (3 attempts, `agent-crashed`) and `test_agent_crash_then_a_fix_still_passes` (PASS on attempt 2) |
| S4 receipt label | reviewer that keeps rejecting: status `PASS-REJECTED`, outside `PASS\|FAIL\|BLOCKED\|TIMEOUT\|ABORTED` | `82cf7c2` | `_assert_documented_reject` on the three-attempt reject, spent scope, spent wiring, and error-beside-accept. Summary starts with `FAIL ` |
| S5 stale worktree | SIGKILL, then a PASS rerun: the killed `local-build-*` path stayed in `git worktree list` | `a12582f` | `test_sigkill_worktree_is_pruned_on_the_next_run`. Recorded path is gone. Sibling `local-build-keep-sibling` stays |

## Fail and recover

| Item | How it fails | How it recovers |
|---|---|---|
| S2 | The loop's elapsed time reaches `--wall-timeout` (default 7200s, env `PFY_LOCAL_BUILD_WALL_TIMEOUT`). Receipt status TIMEOUT, reason `wall-timeout`, exit 3, no commit. A per-agent timeout that is not the wall stays reason `timeout`. Interrupted and mem-edge are not relabelled. | Pass a larger `--wall-timeout`. The worktree from a TIMEOUT is kept because finish unlinks the pid file, so the next run does not prune it. |
| S3 | The agent finishes with a non-zero code and an empty diff (`os._exit(70)` before any write). Receipt FAIL, reason `agent-crashed`, exit 1. It retries while review retries remain. Exit 0 with an empty diff stays `no-change` and still runs the gate. A non-zero exit that wrote files still goes through the gate. | The next attempt can land a real edit and PASS. Fix the agent so it exits 0 after writing the patch. |
| S4 | The gate is green and the review rejects until retries are spent (model reject, scope, or wiring). Receipt status FAIL, reason `review-rejected`, exit 1, summary starts with `FAIL`, no commit. Attempt receipts use the same status. | `--no-review` is the one-attempt path. Or raise `--max-files` / `--max-lines`, or change the patch so the check accepts. Nothing is pushed. |
| S5 | SIGKILL cannot write a receipt. The pid file records the worktree. The next run, and `--reap`, remove that path only when it is under `<repo>/tmp` and the first directory name starts with `local-build-`. Any other registered worktree stays. | Run `./pfy build --local` again, or `./pfy build --local --reap`. A normal FAIL or TIMEOUT keeps its worktree on purpose. |

## Tests

Targeted, `nice -n 19`, `TMPDIR` under this worktree's `tmp/scratch`. No full discover. No local model.

- After S3: `tests.test_pfy_build_local_review` and `tests.test_pfy_build_local`, 102 OK in 170.746s.
- After S4: same two modules, 102 OK in 171.394s.
- After S5: same two modules, 103 OK in 172.054s.

BrokenPipeError and ResourceWarning lines from the stub HTTP server showed up and the runs still exited 0.

## Not taken

Already on base `16f17d8` (the 6664713 review is older than this pin):

- M10: `test_error_field_beside_accept_does_not_commit`
- M17: `test_no_review_does_not_retry_a_red_gate` asserts `review.retries == 0`
- M18: `test_reviewer_prompt_contains_the_changed_line`
- Loose ignored-helper reason: `test_ignored_helper_is_not_committed` expects only `commit-recheck-failed`
- S7: `test_in_scope_rename_is_committed`
- Fault-hook: `PFY_LOCAL_BUILD_INJECT_EXTRA_STAGE` is already described in `docs/ops/HANDOFF-pfy-local-build-mvp.md` under the test seam

No item was skipped for hardware, a secret, or an open question. No ADR.

## Cross-lane

- `docs/ops/HANDOFF-pfy-local-build-mvp.md` still says a larger diff is `PASS-REJECTED`. After S4 that receipt status is `FAIL` and the reason is `review-rejected` (exit 1, no commit). This lane did not edit that file.
- `eval/mvp3/run_trial.py` still special-cases an old `PASS-REJECTED` status. New receipts are `FAIL`, which that scorer already maps to reject. Leave the old branch so older receipts still score. No edit requested.

## Gate

Runtime change in `scripts/pfy_build_local.py`. Gate: Tester plus Reviewer.

Pregate not run: host busy. `Runner.Worker` was live at the start (pid 1225684) and again at the exit (pid 1511538, 2026-11-01T02:29:15Z).

## Next step

Hand `bot/mvp3-s2s5-1031` (head `a12582f`) to Tester and Reviewer. Do not merge from this lane. The operator-doc sentence above is the only follow-up outside this branch.
