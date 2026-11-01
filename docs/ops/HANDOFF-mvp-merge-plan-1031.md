# Handoff: mvp-merge-plan-1031

Lane: `bot/mvp-merge-plan-1031`. Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-merge-plan-1031`. Base: `origin/main` `c0d38afc0f21376e01d0aa57de31d29c2b21d2ca`.
Exit: lane empty at 2026-11-01T01:20:48Z. Wall cap is 2026-11-01T08:16:11Z. Host was not under pressure (MemAvailable about 68 GiB, load about 4, 32 cores, threshold 64).
Pushed artifact: `docs/ops/MERGE-PLAN-1031.md` plus this handoff, the decisions file, and the run log. Scratch merges are not pushed. Nothing was merged to `main`. Nothing was deleted.

## Done

The plan covers every `origin/bot/*-1031` branch plus `origin/bot/mvp3-review-retry` and `origin/bot/backlog-catalog-1030`. Ahead/behind counts are in the plan. The scratch stack is detached at `cee9bdd92bce33df5a8c94c5c77eb376bc242dcd` in `tmp/stack-after`.

| Item | Scratch SHA | Tests | Result |
| --- | --- | --- | --- |
| integrate fast-forward | 1dee0b9 | tmp/integrate-tests.log, 477 tests, 502.110s | OK (skipped=1) |
| mvp3 cherry-pick plus intfix | 215be32 then 49ee477 / 215be32 | tmp/mvp3-tests.log, 104 tests | FAILED 2, fixed in b8d9b64 |
| backlog pfylib.md ours | de91424 | docs only, no product module | recorded |
| cloud-perf, cloudfix, docs, docs-final, quickstart | deb8cb9, 87209ee, 7d04005, 2602fad | tmp/cloud-docs-tests.log, 76 tests | OK, before the timeoutfix union |
| crosslane HEAD wins | 61f0b3e | covered by the later local and cloud runs | recorded |
| dogfood2 union | 90ac258 | tmp/dogfood2-review-tests.log, 90 tests, 144.915s at b8d9b64 | OK |
| review-timeout and warnings fix | b8d9b64 | same 90-test log | OK |
| dsv4 TODO ours, catalog auto-merged | e6baeca | tests.test_catalog_entry_numbers inside the 289 | passed there |
| freshclone, local-t5, gom, realfail2, pass3, mutate-*, review-quality, selfhost2, probe-fix2, timeoutfix | see plan table | tmp/stack-final-tests.log at 9b63b93, 289 tests, 301.767s | 281 passed, 8 failed |
| local-t5 rerun script | 128845d, run at 9b63b93 | 12 tests, 1.077s | OK, ollama trapped |
| expectation fix | 52e3ddc | tmp/stack-rerun-tests.log at 2275c47, 8 tests, 4.355s | OK |
| late retips (dogfood3, selfhost2, cloud-perf, tmpclean) | cee9bdd | tmp/stack-late-tests.log, 3 tests, 0.346s | OK |

Lane commits: `51d51ba` (exit card), `55a138a` (decisions title), `471266eead89a7abbc6a95c25ea7d332dd52b663` (this plan, the handoff, the decisions, and the run log). The run log state line names that SHA.

## Skipped

| Item | Why |
| --- | --- |
| Textual merge of mvp3-followups-1031 | Content-contained in the cherry-pick. Not an ancestor of integrate, so not safe to delete. |
| Textual merge of probe-fix2 and of mvp3-review-retry | Mis-aligned hunks. Cherry-pick used instead. |
| This lane onto the scratch stack | The stack is not pushed. Merging it would only copy the drop-in. |
| 17 branches already inside integrate | Ancestor bit is the evidence. Listed in the plan. Not deleted. |
| Regenerating mutant anchors and review-quality planted diffs | Fail-closed red on the stacked runner. Recovery is named in the plan. Not a merge resolution. |
| `scripts/pregate.sh` | The lane drop-in says not to run it. |
| Local model, `--local`, mutant harness execution, `drive.py`, review-quality model runner | This lane does not need a local model. Targeted unittests only. |
| `docs/TODO.md` on this branch | Shared with other lanes. Scratch resolution is described, not copied here. |

No item was skipped for an open OQ, a secret, or missing hardware. No architecture was invented. The four red tests are a follow-up for the landing, not a new ADR.

## Test evidence

Commands were `nice -n 19 python3 -m unittest ...` with `TMPDIR` under this worktree's `tmp/`. Logs:

- `tmp/integrate-tests.log`: `Ran 477 tests in 502.110s` / `OK (skipped=1)`
- `tmp/mvp3-tests.log`: `Ran 104 tests in 203.424s` / `FAILED (failures=2)` (superseded)
- `tmp/cloud-perf-tests.log`: discard (conflict markers still in the file)
- `tmp/cloud-docs-tests.log`: `Ran 76 tests in 27.883s` / `OK` (before timeoutfix)
- `tmp/dogfood2-review-tests.log`: `Ran 90 tests in 144.915s` / `OK`
- `tmp/stack-final-tests.log`: `Ran 289 tests in 301.767s` / `FAILED (failures=6, errors=2)` plus `Ran 12 tests in 1.077s` / `OK` for the local-t5 rerun
- `tmp/stack-rerun-tests.log`: `Ran 8 tests in 4.355s` / `OK`
- `tmp/stack-late-tests.log`: `Ran 3 tests in 0.346s` / `OK`

Still red after the reruns, same cause, runner not reverted:

- `test_catalog_applies_once_and_parses` (cloud mutants): anchor count 0
- `test_wave5_mutants_each_apply_once_and_parse` (cloud2 mutants): anchor count 0
- `test_catalog_anchors_match_a_copy_of_the_runner` (review mutants): exit 1
- `test_planted_set_shape_and_patches_apply`: patch `b07-shell-rm` does not apply at `scripts/pfy_build_cloud.py:616`

## How changes fail and recover

The pushed branch is docs. The fail/recover behavior lives in the scratch resolutions and is spelled out in `docs/ops/MERGE-PLAN-1031.md` under "How a landing fails and recovers". Short form:

- A review timeout with no out file must be `reviewer-unavailable`, not `review-crashed`. Check timeout first. If that order flips, `test_review_timeout_does_not_commit` fails and the receipt says FAIL.
- Two `"warnings"` keys drop the allow-list warning. One key. If the second key returns, `--no-review` with no allow list has an empty warning list.
- Review timeout after the commit must `_undo_commit` before `as_reject`. If undo is skipped, the rejected commit stays.
- The recheck extract must have its own git repo. If the init is dropped, `test_recheck_git_does_not_walk_up_to_the_caller_repo` fails with PARENT-GIT.
- Phase-clock tests must not use a missing `.git` as the extract marker after that init. Scratch `52e3ddc` is the recovery. The three tests passed.
- Mutant anchors that do not match the union runner fail closed. Recovery is to re-cut them, not to revert the runner.

## Cross-lane requests

- Do not take a TODO edit from this lane. The scratch stack kept integrate's TODO section against mvp3 and against dsv4. Whoever lands the stack should keep that section.
- `docs/modules/pfylib.md`: the longer integrate sentence won over backlog-catalog-1030. The drop-in path it names is `docs/build-dropins/pfy-local-build-mvp3.md` on `bot/mvp3-review-retry` until that branch lands.
- This lane did not edit files owned by another lane's checkout. Scratch worktrees are under this lane's `tmp/`.

## Gate

Pushed commits are docs, decisions, the run log, and the plan. Gate for this branch: pregate plus Reviewer.

Pregate not run: the lane drop-in says "Do not run scripts/pregate.sh".

The scratch stack is runtime. It is not on this branch. Landing it needs Tester plus Reviewer, plus a fresh fetch, plus a re-cut of the four stale anchor tests.

## Next step

On a new integration branch, not on `main`: fast-forward to `1dee0b9`, replay the scratch line in `docs/ops/MERGE-PLAN-1031.md`, and include scratch commit `52e3ddc`. Fetch first. Any subject that is not in `cee9bdd` needs the same merge. Then re-cut the four red anchor tests and run those modules. The 17 integrate ancestors are safe to delete only after you are keeping that integrate tip or a descendant. The cherry-picked branches are not safe to delete until the replay is on a branch you keep.
