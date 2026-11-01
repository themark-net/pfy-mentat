# Merge plan 1031

Scratch stack only. Nothing here is merged to `main`. Nothing is deleted. The scratch tip is not pushed.

Freeze: `cee9bdd92bce33df5a8c94c5c77eb376bc242dcd` at 2026-11-01T01:20:48Z, detached worktree `tmp/stack-after`.
Base: `origin/main` `c0d38afc0f21376e01d0aa57de31d29c2b21d2ca`.
Integration: `origin/bot/mvp-integrate-1031` `1dee0b91bda11ba1fcda87819423437a3f10f289` (0 behind, 522 ahead). That tip is an ancestor of the scratch stack.
Counts below are `git rev-list --left-right --count origin/main...branch` (behind, then ahead) at freeze time. Other lanes were still pushing. A subject scan at freeze found no non-merge commit on those branches whose subject is missing from the scratch stack, except this lane, which is not merged onto the stack.

Order used: integration fast-forward, intfix, mvp3 cherry-pick, backlog, then the other not-contained branches alphabetically, skipping this lane. Tips that moved after their first merge were merged again. `origin/bot/mvp3-followups-1031` was not textually merged. `origin/bot/mvp-probe-fix2-1031` was cherry-picked, not textually merged.

## Safe to delete later

These tips are ancestors of `origin/bot/mvp-integrate-1031`. Do not delete them in this lane. Deleting is safe only after that integrate tip is the one you keep.

| Branch | Tip | Behind | Ahead |
| --- | --- | --- | --- |
| bot/mvp-backlog-burn-1031 | 84db544 | 0 | 247 |
| bot/mvp-ci-cover-1031 | 7391cd6 | 0 | 231 |
| bot/mvp-cloud-1031 | d94d2b6 | 12 | 17 |
| bot/mvp-dogfood-1031 | e404b42 | 12 | 35 |
| bot/mvp-dogfood-fix-1031 | 1fa9fd3 | 0 | 241 |
| bot/mvp-eval-1031 | 1768037 | 12 | 12 |
| bot/mvp-followups-fix2-1031 | aea15bf | 0 | 21 |
| bot/mvp-mutate-preflight-1031 | 322cde0 | 0 | 237 |
| bot/mvp-preflight-1031 | 100348d | 12 | 5 |
| bot/mvp-realfail-1031 | d09647a | 12 | 33 |
| bot/mvp-realfail3-1031 | a4c80a1 | 0 | 240 |
| bot/mvp-review-fix-1031 | 1140434 | 12 | 16 |
| bot/mvp-review-fix2-1031 | 8c40087 | 12 | 49 |
| bot/mvp-selfhost-1031 | 5fb063e | 12 | 61 |
| bot/mvp-sixtask-1031 | 177940e | 12 | 65 |
| bot/mvp-sixtask-int-1031 | d642ec1 | 0 | 258 |
| bot/mvp-surface-1031 | 30cdd24 | 12 | 5 |

`bot/mvp-integrate-1031` itself is the container. Do not delete it.

## Not safe to delete

Content can be on the scratch stack and still be unsafe to delete. The scratch tip is a detached worktree under `tmp/` and is not on origin. Cherry-picks have different SHAs, so `git merge-base --is-ancestor` is no. Delete these only after their commits are reachable from a branch you keep.

| Branch | Tip | Behind | Ahead | Why it is not an ancestor of integrate |
| --- | --- | --- | --- | --- |
| bot/mvp-intfix-1031 | 1c64e50 | 2 | 92 | Cherry-picked as `215be32`. Handoff file matches. |
| bot/mvp3-followups-1031 | ffce7a7 | 0 | 43 | Every non-merge subject is in the mvp3 cherry-pick. Not merged again. |
| bot/mvp3-review-retry | d2521b5 | 0 | 50 | Cherry-picked. A textual merge conflicts. |
| bot/mvp-probe-fix2-1031 | 67e52e1 | 0 | 55 | Cherry-picked, including the hardlink fix. A textual merge conflicts. |
| bot/mvp-merge-plan-1031 | 55a138a | 0 | 3 | This lane. Not merged onto the stack. |

Every other `bot/*-1031` tip in the table below was merged, and at freeze its non-merge subjects are in the scratch stack. Those branches are still not ancestors of integrate, so they are not in the safe-to-delete list.

## Ahead and behind at freeze

| Branch | Tip | Behind | Ahead | In integrate |
| --- | --- | --- | --- | --- |
| bot/backlog-catalog-1030 | 1f3b1a3 | 0 | 18 | no |
| bot/mvp-backlog-burn-1031 | 84db544 | 0 | 247 | yes |
| bot/mvp-ci-cover-1031 | 7391cd6 | 0 | 231 | yes |
| bot/mvp-cloud-1031 | d94d2b6 | 12 | 17 | yes |
| bot/mvp-cloudfix-1031 | 10b4f5b | 0 | 252 | no |
| bot/mvp-cloud-perf-1031 | 7c7ca94 | 0 | 469 | no |
| bot/mvp-crosslane-1031 | 2fac946 | 0 | 335 | no |
| bot/mvp-daily-card-1031 | a1908f9 | 2 | 92 | no |
| bot/mvp-docs-1031 | 6c79725 | 2 | 98 | no |
| bot/mvp-docs-final-1031 | 0582208 | 0 | 526 | no |
| bot/mvp-dogfood-1031 | e404b42 | 12 | 35 | yes |
| bot/mvp-dogfood-fix-1031 | 1fa9fd3 | 0 | 241 | yes |
| bot/mvp-dogfood2-1031 | ac42593 | 0 | 277 | no |
| bot/mvp-dogfood3-1031 | f50192a | 0 | 540 | no |
| bot/mvp-dsv4-1031 | 815185c | 0 | 22 | no |
| bot/mvp-eval-1031 | 1768037 | 12 | 12 | yes |
| bot/mvp-followups-fix2-1031 | aea15bf | 0 | 21 | yes |
| bot/mvp-freshclone-1031 | 4bddf25 | 0 | 232 | no |
| bot/mvp-gom-dogfood-1031 | 88a841b | 0 | 252 | no |
| bot/mvp-integrate-1031 | 1dee0b9 | 0 | 522 | yes |
| bot/mvp-intfix-1031 | 1c64e50 | 2 | 92 | no |
| bot/mvp-local-t5-1031 | c629ae7 | 0 | 237 | no |
| bot/mvp-merge-plan-1031 | 55a138a | 0 | 3 | no |
| bot/mvp-mutate-cloud-1031 | 9f707fd | 12 | 63 | no |
| bot/mvp-mutate-cloud2-1031 | 82a52ce | 0 | 471 | no |
| bot/mvp-mutate-preflight-1031 | 322cde0 | 0 | 237 | yes |
| bot/mvp-mutate-review-1031 | 0160ac4 | 12 | 44 | no |
| bot/mvp-pass3-review-1031 | cc338de | 0 | 528 | no |
| bot/mvp-plan-1031 | 6d449ec | 12 | 4 | no |
| bot/mvp-preflight-1031 | 100348d | 12 | 5 | yes |
| bot/mvp-probe-fix2-1031 | 67e52e1 | 0 | 55 | no |
| bot/mvp-realfail-1031 | d09647a | 12 | 33 | yes |
| bot/mvp-realfail2-1031 | 44b28d4 | 12 | 93 | no |
| bot/mvp-realfail3-1031 | a4c80a1 | 0 | 240 | yes |
| bot/mvp-review-fix-1031 | 1140434 | 12 | 16 | yes |
| bot/mvp-review-fix2-1031 | 8c40087 | 12 | 49 | yes |
| bot/mvp-review-quality-1031 | 0930690 | 0 | 468 | no |
| bot/mvp-selfhost-1031 | 5fb063e | 12 | 61 | yes |
| bot/mvp-selfhost2-1031 | 2a69b02 | 0 | 262 | no |
| bot/mvp-sixtask-1031 | 177940e | 12 | 65 | yes |
| bot/mvp-sixtask-int-1031 | d642ec1 | 0 | 258 | yes |
| bot/mvp-surface-1031 | 30cdd24 | 12 | 5 | yes |
| bot/mvp-timeoutfix-1031 | 272bd28 | 0 | 538 | no |
| bot/mvp-tmpclean-1031 | 3017700 | 2 | 94 | no |
| bot/mvp-tmpclean2-1031 | e7f654a | 0 | 33 | no |
| bot/mvp3-followups-1031 | ffce7a7 | 0 | 43 | no |
| bot/mvp3-review-retry | d2521b5 | 0 | 50 | no |

## Scratch SHAs

Worktrees, all detached, none pushed:

| Worktree | Role | Tip to keep |
| --- | --- | --- |
| tmp/merge-scratch | integrate fast-forward and its suite | 1dee0b9 |
| tmp/conflict-mvp3 | mvp3 cherry-picks plus intfix | 215be32 |
| tmp/stack-next | dogfood2 merge plus the review-timeout fix | b8d9b64 |
| tmp/stack-after | stack from dogfood3 onward | cee9bdd |

Stack line on `tmp/stack-after` (oldest first, after integrate `1dee0b9`):

| Scratch SHA | What landed |
| --- | --- |
| 41fc6f8..49ee477 | mvp3-review-retry and followups, cherry-pick, 31 non-merge commits |
| 215be32 | intfix handoff cherry-pick of 1c64e50 |
| de91424 | backlog-catalog-1030 |
| deb8cb9 | mvp-cloud-perf-1031 first merge |
| 87209ee | mvp-cloudfix-1031 |
| 61f0b3e | mvp-crosslane-1031 |
| 99e8c2d | mvp-daily-card-1031 |
| 7d04005 | mvp-docs-1031 |
| 2602fad | mvp-docs-final-1031 |
| 90ac258 | mvp-dogfood2-1031 |
| b8d9b64 | review-timeout and warnings-key fix found by the mvp3 suite |
| 18d9326 | mvp-dogfood3-1031 first merge |
| e6baeca | mvp-dsv4-1031 |
| d54fb6a | mvp-freshclone-1031 |
| 744fe76 | mvp-gom-dogfood-1031 |
| 128845d | mvp-local-t5-1031 |
| 31b65ab | mvp-mutate-cloud-1031 |
| 276063e | mvp-mutate-cloud2-1031 |
| 3a95e1f | mvp-mutate-review-1031 |
| b8aff6b | mvp-pass3-review-1031 |
| cf5e0ef | mvp-plan-1031 |
| 1662500, aa787cc, b7d4309 | probe-fix2 drop-in, exit card, executable-bit digest |
| 51afda3 | mvp-realfail2-1031 |
| 14442c7 | mvp-review-quality-1031 |
| e4557f9 | mvp-selfhost2-1031 first merge |
| 3ccc204 | mvp-timeoutfix-1031 first merge |
| 9b3f41c | dogfood3 retip (smoke_098, smoke_103) |
| d7b3914, 29f6071 | probe-fix2 hardlink fix and handoff |
| 704549f | mvp-tmpclean-1031 |
| a837802 | mvp-tmpclean2-1031 |
| 9b63b93 | timeoutfix retip (run-log line only) |
| 52e3ddc | test expectations for the winning runner |
| 2275c47 | selfhost2 retip (surface symlink, adapter install symlink) |
| 07e283d | cloud-perf retip (receipts only) |
| 7666f13 | dogfood3 retip (smoke_106) |
| cee9bdd | selfhost2 retip (hedge ledger symlink) |

## Conflict resolutions

Policy: union when both sides add different fail-closed behavior or different tests. On a true line clash, the stricter check wins. Shared docs keep integrate wording and fold in incoming rows that are not already stated. Lane-owned handoff, run log, decisions, and drop-in files keep the incoming lane. Add/add keeps the later, longer file when the other side is an older drop-in.

### mvp3-review-retry (cherry-pick, not a textual merge)

A full `git merge` mis-aligned large adjacent additions. Aborted. Cherry-pick of the 31 non-merge commits. `docs/TODO.md` stays the integrate text. mvp3's TODO drops the integrate section and reopens T-0070, T-0074, T-0095, and T-0002. That older TODO loses.

Code unions in `scripts/pfy_build_local.py` and the local tests:

- Test seam: incoming `_test_seam_on()` wins. Same predicate as the scattered checks it replaced.
- Missing review out file: keep integrate's stale-worktree helpers and outage classifier, and keep incoming `_review_poster_argv`. A missing out file after a non-timeout exit is status `crashed`, reasons `review-crashed`, verdict `reject`. Do not return `http-error`. That string falls through and retries.
- Gate rewrite: keep the reviewed-digest assignment and integrate's empty-diff crash handler. Do not take incoming `if not changed: run_tests(...)`.
- Symlink diff test stub: union. The gitdir loop stays inside the plan scenario.
- Review HTTP handler: keep integrate's `review_http_status` default 200 that sends `review-down`, then incoming `review_raw`, then the existing queue and the second status check.

followups is an ancestor of review-retry on the origin branch and is content-contained in this cherry-pick. Do not textual-merge it.

### intfix

Cherry-pick `1c64e50` as `215be32`. Docs only (the intfix handoff). The handoff blob on the scratch stack matches the branch.

### backlog-catalog-1030 (`de91424`)

Conflict: `docs/modules/pfylib.md`. Ours wins. The incoming sentence is shorter and older, and it is not from the unique hygiene commit `1f3b1a3`. The tree delta versus `215be32` is the mvp2 handoff sentence. The sentence on the stack names the drop-in path `docs/build-dropins/pfy-local-build-mvp3.md`, which lives on `bot/mvp3-review-retry` until that branch lands.

### crosslane (`61f0b3e`)

`git merge-tree` had called this clean before the mvp3 cherry-pick. After that cherry-pick the merge conflicted, and HEAD won all four code hunks.

- `_stage_reviewed`: excludes first, then `:(literal)` paths, inside `if wanted:`, using `_test_seam_on()`. Crosslane put the literal paths first. On git 2.53 an exclude after a positive pathspec drops an untracked path.
- Missing out file: status `crashed`, reasons `review-crashed`, verdict `reject`.
- Receipt keeps `"reviewer": "same local model as the agent"` next to `"same_model": true`.
- `test_ignored_helper_is_not_committed` keeps `data["reason"] == "commit-recheck-failed"`.

### docs-final (`2602fad`)

Add/add on `docs/QUICKSTART-pfy-build.md` after docs-1031 had already added that path. A preview that said clean went stale. Took docs-final (`--theirs`) and then put the walkthrough link back into the intro.

Winner for the body: docs-final. It is the later measured card. It adds `--writable-test`, the stricter `--base` rule (when HEAD is not origin/main, a dry-run without `--base` exits 2), and the runnable fence `./pfy build "quickstart dry run" --dry-run --base HEAD --receipt-dir "$PWD/tmp/quickstart-dry-run"`. `tests/test_quickstart_commands.py` re-runs fences tagged `bash runnable exit=N`.

Intro union: "One card for the daily command. Cloud Grok, review on, nothing pushed. The longer operator card is pfy-build-daily.md. Line-by-line proof: MVP-DOD-WALKTHROUGH.md. Measured GO and the six PASS lines: VERDICT.md."

### dogfood2 (`90ac258`)

- `tree_sig` in smoke_112_114, smoke_115_116, smoke_117_118, smoke_119_121: union. Keep the root-symlink hash (lstat mode plus readlink), file size, and streamed sha256. Call `rglob("*", recurse_symlinks=False)`. A non-file non-link is `other`. Directories stay `dir`. mtime stays out of `tree_sig`. Do not drop size.
- smoke_112 overtime names: dogfood2 wins. `stop_timeout_reason` and `timeout_step = "overtime"`. The home check runs before the stop-timeout return, and a stop timeout is still a failure after that check.
- smoke_122_124 imports: both `signal` and `stat`.
- smoke_148 `home_sig`: HEAD wins (stricter). Structured tuples with mode, mtime_ns, size, and streamed digest. Symlinks are not opened. Missing is None. Unreadable is recorded, not raised. `test_home_sig_148.py` requires an mtime-only touch to change the signature.
- `tests/test_mvp2_t3_daemon_stop.py`: HEAD wins. Scratch stays under the repo `tmp/` via `tempfile.TemporaryDirectory(..., dir=scratch)`. A bare `TemporaryDirectory` can land in `/tmp`.
- `tests/test_remaining_home_sigs.py`: smoke_148 records mtime, smoke_149 leaves mtime out. Do not revert smoke_149.
- smoke_109_111, the dogfood2 receipts, and the new tests auto-merged. `scripts/pregate.sh` auto-merged and was not run.

### review-timeout fix (`b8d9b64`)

Not an incoming branch. The mvp3 suite failed two tests because the cherry-pick union had two bugs. Fixed on the scratch stack before later merges.

- A bounded-call timeout that leaves no out file was classified as `crashed` before the timeout check, so the receipt was FAIL instead of `reviewer-unavailable`. Timeout is checked first (`overall-timeout`, then plain `timeout` returns `unavailable`). A missing out file after a non-timeout exit is still `crashed`. HTTP body errors still return `unavailable` via `_review_transport_error` / `_review_outage_kind`. Do not return `http-error`.
- `finish()` had two `"warnings"` keys. The second overwrote the early allow-list warning, so `--no-review` with no allow list produced an empty list. One key: `list(dict.fromkeys([*warnings, *([scope_warning] if scope_warning else [])]))`. The early warning string stays `no allow list: scope was not checked.`. The review-path phrase `scope check skipped: no allow list` is set only when review runs.

### dsv4 (`e6baeca`)

Conflict: `docs/TODO.md` only. The integrate section was on HEAD and absent on theirs. Kept the section. Incoming catalog rows auto-merged (TOOLS.md, catalog JSON, source entry, eval report). Do not copy a TODO edit from this resolution onto `bot/mvp-merge-plan-1031`. TODO is shared with other lanes.

### mutate-cloud2 (`276063e`)

Add/add. mutate-cloud had just created `eval/mutation-1031/cloud/run_mutants.py` and the results JSON, so a preview that said clean went stale. cloud2 (`--theirs`) wins those paths. cloud2 keeps `MUTANTS` as C1-C16 and adds `CLOUD2_MUTANTS` C17-C43. `main()` runs the combined catalog. `cloud_modules` globs both `test_mut_cloud_*.py` and `test_mut_cloud2_*.py` and skips `*_harness`. `first_detail` prefers a `FAIL: test_` / `ERROR: test_` / AssertionError / Traceback line over a generic `FAIL:` reason. REPORT.md was hand-unioned: cloud2 intro, one sentence that the C1-C16 raw rows stay on `origin/bot/mvp-mutate-cloud-1031` while the JSON here is the wave-5 run, then both tables, then the cloud2 re-run section (`--timeout 180`). Do not run `run_mutants.py`.

### plan-1031 (`cf5e0ef`)

Add/add `docs/build-dropins/mvp-integrate-1031.md`. HEAD wins (pass 2 and pass 3 addenda). Theirs was the original drop-in with that region empty. The rest of the plan branch auto-merged.

### probe-fix2 (cherry-pick)

A textual merge conflicts on `docs/TODO.md`, `scripts/pfy_build_local.py`, and both local test files, same shape as review-retry. Cherry-pick the commits whose subjects were not already on the stack:

- `0486712` drop-in, as `1662500`
- `8ce94e3` exit card, as `aa787cc`
- `29da017` executable-bit digest, as `b7d4309`. `_reviewed_digest` records `100644` or `100755` when `core.filemode` is on. A mode git will not record stays equal.
- `915edf0` hardlink whose other name is outside the worktree, as `d7b3914`. This commit landed after the first three picks. It applied clean.
- `67e52e1` handoff, as `29f6071`

### timeoutfix (`3ccc204`, retip `9b63b93`)

`git merge-tree --write-tree` conflicted. The old `git merge-tree BASE OURS THEIRS` form listed extra files. Trust write-tree and the real merge. Conflicts: `scripts/pfy_build_cloud.py` (six hunks) and `tests/test_pfy_build_cloud.py` (one inserted test, three hunks).

Keep the stack's commit-then-overlap review and the parallel post-change gates. Add timeoutfix's run budget.

- `arm(False)` before the post-change gates, so a review-reject retry's extended timeout does not apply to the gate.
- `if again is None: arm(False); again = self.gate()`. Do not run a third gate when the parallel pair already set `again`.
- Before the commit: if `time_left() < 0.05`, a retry that already rejected returns `as_reject` (stays review-rejected). A first timeout records TIMEOUT. Then `arm(False)`, set `review_truncated`, commit, then `_overlap_review_recheck`. Taking theirs' direct `grok_call` would NameError, because the auto-merged tail unpacks `review_row, recheck_row`.
- On review `timeout`: `_undo_commit(keep_edits=True)` first. `as_reject` does not undo. If `last_reject` is set, return `as_reject`. Otherwise record TIMEOUT.
- No-review root or symlink reject: set `last_reject = ["review-rejected"]` and keep both messages (symlink `:target` versus recursive delete).
- Theirs' `arm(False)` before `commit_paths` was indented at the for-loop level. Keep it inside the else, then `commit_paths`.

`recheck_sha` already inits a nested git repo with `core.hooksPath` so `git rev-parse --show-toplevel` stays inside the extract. `gate()` sets TMPDIR to the extract tmp when cwd is the extract. Both tests are kept:

- `test_recheck_tmpdir_stays_inside_the_extract`
- `test_recheck_git_does_not_walk_up_to_the_caller_repo`

The retip `9b63b93` is one run-log line. Clean.

### Later retips (clean)

Fetched again because lanes were still pushing. Merged when the subject was not already on the stack.

- dogfood3 `9b3f41c`: smoke_098 and smoke_103 bad-timeout tests, plus receipts for smoke_137, smoke_098, and smoke_103.
- dogfood3 `7666f13`: smoke_106 bad-timeout test and receipt. Tip `f50192a`.
- selfhost2 `2275c47`: harness surface symlink, adapter install symlink, `pfylib/adapters/base.py`.
- selfhost2 `cee9bdd`: hedge ledger symlink (`pfylib/hedge.py`, `tests/test_hedge_ledger_symlink.py`). Tip `2a69b02`.
- cloud-perf `07e283d`: perf report and timeout-rows JSON. Docs and receipts. Tip `7c7ca94`.
- tmpclean `704549f` and tmpclean2 `a837802`: handoff docs only.

### Test expectations (`52e3ddc`)

Not from a branch. The timeoutfix nested git repo made three phase-clock tests and the signal test treat the extract as an ordinary git worktree, because they used "no `.git`" as the extract marker. Updated the probes to treat a directory named `recheck-*` whose toplevel is itself as the extract. The first-day help assertion now requires the stricter sentence (`Required when HEAD is not origin/main` and `else HEAD if origin/main is absent`) instead of `origin/main if it exists, else HEAD`. The looser sentence loses because docs-final's `--base` rule is the one on the stack.

## Clean merges with no conflict note above

cloudfix `87209ee` (docs), daily-card `99e8c2d` (docs), docs `7d04005` (README, QUICKSTART, `tests/test_quickstart_commands.py`), freshclone `d54fb6a` (`tests/test_pfy_build_first_day.py` plus docs), gom-dogfood `744fe76` (docs and receipts), local-t5 `128845d` (`eval/mvp-1031/test_rerun_local.py`, not executed as a local model), mutate-cloud `31b65ab`, mutate-review `3a95e1f`, pass3-review `b8aff6b` (`scripts/check_workflow_image_pin.py`), realfail2 `51afda3`, review-quality `14442c7`, selfhost2 first merge `e4557f9`.

Contained branches were not merged again.

## Tests

Niced `python3 -m unittest`. TMPDIR is this worktree's `tmp/`. No local model. No `--local`. `eval/mvp-1031/test_rerun_local.py` traps `ollama` on PATH and does not call `127.0.0.1:11434`. Mutant harnesses, `drive.py`, and the review-quality model runner were not executed. `scripts/pregate.sh` was not run.

| Log | SHA the tests ran against | Result |
| --- | --- | --- |
| tmp/integrate-tests.log | 1dee0b9 (integrate fast-forward) | Ran 477 tests in 502.110s, OK (skipped=1) |
| tmp/mvp3-tests.log | 215be32 | Ran 104 tests in 203.424s, FAILED 2. Superseded by the review-timeout fix. |
| tmp/cloud-perf-tests.log | during an unresolved merge | FAILED 1. Conflict markers were still in the file. Discard. |
| tmp/cloud-docs-tests.log | before timeoutfix and review-quality | Ran 76 tests in 27.883s, OK. Not evidence for the final cloud runner. |
| tmp/dogfood2-review-tests.log | b8d9b64 on tmp/stack-next | Ran 90 tests in 144.915s, OK. Review module plus dogfood2 smokes. |
| tmp/stack-final-tests.log | 9b63b93 | Ran 289 tests in 301.767s, FAILED (failures=6, errors=2). local-t5 rerun: Ran 12 tests in 1.077s, OK. |
| tmp/stack-rerun-tests.log | 2275c47 | Ran 8 tests in 4.355s, OK. The four expectation failures plus the adapter and surface symlink tests. |
| tmp/stack-late-tests.log | cee9bdd | Ran 3 tests in 0.346s, OK. smoke_106 bad timeout and hedge ledger symlink. |

The 289-test run covered the modules touched by dogfood3, freshclone, mutate-cloud, mutate-cloud2, mutate-review, pass3, realfail2, review-quality, selfhost2 (first merge), probe-fix2 including the hardlink fix, timeoutfix, phase clock, quickstart, and `tests.test_catalog_entry_numbers`. 281 of those tests passed. Four failures were the stale "no `.git`" and first-day help expectations, and they passed on the rerun. Four remain red. See below.

dogfood2 smoke modules were not re-run after b8d9b64. Later merges did not change those smoke files.

`tests.test_pfy_build_local` and `tests.test_pfy_build_local_review` passed inside the 289-test run, which is after the digest change and the hardlink cherry-pick. Later commits did not edit `scripts/pfy_build_local.py`.

`tests.test_pfy_build_cloud` passed inside that same run, after the timeoutfix union, including both recheck tests. Later commits did not edit `scripts/pfy_build_cloud.py`.

## Still red on the stacked runner

These four tests failed at `9b63b93` and were not changed afterward. The files they anchor were edited by later merges (timeoutfix, review-quality, selfhost2, probe-fix2). The harness fails closed when an anchor is missing. That is the right failure. This lane did not regenerate anchors or planted diffs.

| Test | What failed | Recovery tomorrow |
| --- | --- | --- |
| tests.test_mut_cloud_harness.HarnessBehaviorTests.test_catalog_applies_once_and_parses | ApplyError anchor count 0 | Re-cut C1-C16 anchors against the union cloud runner. Do not revert the runner. |
| tests.test_mut_cloud2_harness.Cloud2CatalogTests.test_wave5_mutants_each_apply_once_and_parse | ApplyError anchor count 0 | Re-cut C17-C43 the same way. |
| tests.test_mut_review_harness.HarnessBehaviorTests.test_catalog_anchors_match_a_copy_of_the_runner | check_anchors returned 1 | Re-cut R1-R14 against the union local runner (digest, hardlink, timeout order). |
| tests.test_review_quality_replay.ReviewQualityReplayTests.test_planted_set_shape_and_patches_apply | b07-shell-rm does not apply at scripts/pfy_build_cloud.py:616 | Regenerate the planted diffs against the union runner. |

## How a landing fails and recovers

- Textual merge of mvp3 or probe-fix2 onto integrate drops integrate-only helpers or mis-aligns hunks. Recover: cherry-pick, then run `tests.test_pfy_build_local` and `tests.test_pfy_build_local_review`.
- Classifying a review timeout as `crashed` records FAIL instead of `reviewer-unavailable`. Recover: check timeout before the missing-file path. The rerun of the review module at `b8d9b64` passed.
- A second `"warnings"` key drops the allow-list warning. Recover: one key. Same rerun.
- Taking timeoutfix's review call and dropping `_overlap_review_recheck` NameErrors on `review_row`. Recover: budget check, then commit, then overlap. `tests.test_pfy_build_cloud` passed at `9b63b93`.
- Calling `as_reject` on a review timeout without `_undo_commit` leaves the commit in place. Recover: undo first.
- Dropping the nested git init in the extract brings back the kolibri walk-up. Recover: keep the init. `test_recheck_git_does_not_walk_up_to_the_caller_repo` passed.
- Treating "no `.git`" as the extract marker fails the phase-clock counts after that init. Recover: scratch commit `52e3ddc`. The three tests passed at `2275c47`.
- cloud2 add/add resolved the wrong way loses C17-C43 or loses the C1-C16 catalog. Recover: cloud2 file, which contains both. Anchor tests stay red until the anchors are re-cut. That red is expected.
- Putting excludes after a positive pathspec on git 2.53 drops an untracked path. Recover: excludes first, as in the crosslane resolution.
- A bare `TemporaryDirectory` in the daemon-stop test writes under `/tmp`. Recover: `dir=` under the repo `tmp/`.

## Tomorrow

1. Fast-forward `origin/main` to integrate `1dee0b9` on a new integration branch. Do not merge to `main` from this plan.
2. Replay the scratch line above. Prefer the resolutions in this file over a fresh textual merge of mvp3, followups, or probe-fix2.
3. Carry scratch commit `52e3ddc` with the replay. It is the test update for the nested recheck repo and the stricter `--base` help.
4. Re-cut the four stale anchor and planted-diff tests, then run those modules.
5. The 17 ancestor branches are safe to delete after you confirm you are keeping integrate `1dee0b9` or a descendant. Do not delete the cherry-picked branches until the replay is on a branch you keep.
6. Tips moved during this run. Fetch again before the real landing. Merge any subject that is not already in the replay.
