# Handoff mvp-integrate-pass4-1031

Pass 4 integrated the ten finished wave 6-7 lanes onto `bot/mvp-integrate-pass4-1031`. No rebase, no force push, no PR, no merge to main, no tag. Not a Feature GO. Catalog HOLD 70-75 unchanged. No local model. No `--local`. This lane did not run `scripts/pregate.sh`.

Caller tip at the demo: `f6d1a3b`. The handoff commit is the tip to review.

## Merge table

| Branch | Tip | Result |
|--------|-----|--------|
| `origin/bot/mvp-localbench-tmpdir-1031` | `76fd6a1` | Clean. Merge `2279366`. `tests.test_local_bench` 18 OK in 1.343s |
| `origin/bot/mvp-probe-int-1031` | `b2cbd4f` | Clean. Merge `450c339`. `tests.test_pfy_build_cloud` 67 OK in 21.580s |
| `origin/bot/mvp-pass3-review-1031` | `cc338de` | Clean. Merge `3122349`. `tests.test_workflow_image_pin` 33 OK in 20.244s |
| `origin/bot/mvp-dogfood3-1031` | `f50192a` | Clean. Merge `8e9354d`. Ten smoke modules, 119 OK in 29.411s |
| `origin/bot/mvp-hermes-check-1031` | `61396e4` | Clean. Merge `7689bcb`. `tests.test_hermes_bakeoff` 32 OK, skipped 1, in 3.187s |
| `origin/bot/mvp-timeoutfix-1031` | `ef622a6` | Three conflicts in `scripts/pfy_build_cloud.py`. Kept probe-int symlink checks and the timeoutfix budget helpers. Merge `d6c2cbf`. 88 OK, skipped 1, in 32.644s |
| `origin/bot/mvp-cloud-perf-1031` | `7c7ca94` | Six conflicts in `scripts/pfy_build_cloud.py`. Kept the phase clock, parallel post gates, review overlap, symlink checks, and budget helpers. Merge `6b89b7a`. 99 OK, skipped 1, in 44.249s |
| `origin/bot/mvp-selfhost2-1031` | `c51c0b3` | Clean. Merge `38002cb`. Symlink modules 150 OK in 70.509s, then related modules 112 OK in 4.038s |
| `origin/bot/mvp-mutate-cloud2-1031` | `82a52ce` | Clean merge `e8534cf`. Anchors C9, C22, C38, and C39 retargeted in `7ad4a40`. 17 OK in 13.433s |
| `origin/bot/mvp-review-quality-1031` | `0930690` | Clean merge `2fd2625`. Planted diffs b09 and g07 retargeted in `da6542c`. Replay 7 OK in 0.275s |

Not merged, on purpose: mvp3 branches, backlog branches, and `bot/mvp-probe-fix2-1031`. A refetch at 2026-11-01T04:22Z still showed each tip contained.

## Suite

Command shape: `TMPDIR=$PWD/tmp/suite-pass4 nice -n 19 flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock python3 -m unittest discover -s tests -t .`

G0 was idle (`pgrep -x Runner.Worker` found nothing). The flock waited behind another lane. This lane did not run pregate. Discover ran on tree `3c712b1`.

Ran 1320 tests in 938.736s. Failures 1, skipped 16.

The failure was `tests.test_selfhost_1031_log.SelfhostBuiltByTests.test_this_branch_has_no_bad_built_by_trailer`. The same test on base `1dee0b9` was OK, so the merges brought it. Commit `bbd8254` accepts the hard 72-character subject, the current ellipsis subject, and thirteen amended selfhost2 cherry-picks keyed by sha and receipt path. A third subject form still fails. Targeted rerun: 3 OK in 0.114s. No second discover.

## Demo

FAIL. Checker `python3 eval/mvp-1031/check_receipt.py eval/mvp-1031/demo-receipt-pass4.json` exit 1 (`status is not PASS`). Receipt [../../eval/mvp-1031/demo-receipt-pass4.json](../../eval/mvp-1031/demo-receipt-pass4.json). Report [../../eval/mvp-1031/REPORT.md](../../eval/mvp-1031/REPORT.md).

Throwaway clone `tmp/demo4-target`, branch `demo-base`, caller `f6d1a3b`. One cloud `./pfy build`, no `--local`. Wall 1640 seconds (2026-11-01T03:53:42Z to 2026-11-01T04:21:02Z). Exit 1. Attempts 3. No branch. No commit. Review reject. Human verdict no. The integrate checkout stayed `bot/mvp-integrate-pass4-1031`. The clone stayed on `demo-base`.

Task: protect `.env.bak` and `.env.local` (any `.env.*` basename except `.env.example`) and add one behavior test. Gate before exit 1 (the test method was absent). Gate after exit 0. Review said the rule and the test match the task, and the diff also edits shared `_run` (it strips `GIT_DIR`) and removes the fixture receipt directory with `shutil.rmtree`. This lane agrees with the reject. No second cloud build.

The protect rule is still open on this branch.

## How this pass fails and recovers

- Cloud subject check: a Built-by commit whose subject is neither the hard 72 cut nor `commit_subject` fails, unless it is one of the thirteen listed cherry-picks and the receipt path still matches. Recovery is to use a runner subject. Rewriting the thirteen commits was not done.
- Merge conflicts in `scripts/pfy_build_cloud.py`: dropping either side fails that side's tests. Recovery is the merge that kept both. The targeted cloud modules passed after each conflict.
- Demo: review reject leaves no commit. Recovery is a smaller patch that does not edit `_run`. This lane did not write that patch.

## Cross-lane requests

- Land the dotenv basename rule in `scripts/pfy_build_cloud.py` without editing `tests/test_pfy_build_cloud.py` helper `_run`. The cloud demo's diff is not on this branch.
- mvp3 branches, backlog branches, and `bot/mvp-probe-fix2-1031` stay out.

## Gate

Tester plus Reviewer. The merges brought runtime files, including `scripts/pfy_build_cloud.py`. This lane's own edit after the merges is the Built-by test (`bbd8254`), the demo receipt, and this handoff.

Pregate not run. The drop-in forbids `scripts/pregate.sh` in this lane. At suite start another pregate already held the heavy lock.

## Next

Operator runs Tester plus Reviewer, then pregate, on this tip. No further named wave 6-7 tip is unmerged. Exit: lane empty.
