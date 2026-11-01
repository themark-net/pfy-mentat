# RUN-LOG mvp-merge-plan-1031

Start: 2026-10-31T17:36:11-0700 (2026-11-01T00:36:11Z).
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-merge-plan-1031`
Branch: `bot/mvp-merge-plan-1031`
Base: `origin/main` `c0d38afc0f21376e01d0aa57de31d29c2b21d2ca`
Lane tip at plan time: `a988d34f5becde2eb288ebd80b91f71213989a6c` (0 behind, 1 ahead of origin/main: the drop-in).
Decisions: `docs/ops/AUTONOMOUS-DECISIONS-mvp-merge-plan-1031.md`
Handoff: `docs/ops/HANDOFF-mvp-merge-plan-1031.md`
Plan doc (only merge artifact that is pushed): `docs/ops/MERGE-PLAN-1031.md`
Needs a local model: no.

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria): every origin/bot/*-1031 branch, plus origin/bot/mvp3-review-retry and origin/bot/backlog-catalog-1030, has an ahead/behind count versus origin/main. A scratch worktree under this worktree's tmp/ test-merges them onto origin/main in the order integration, mvp3, backlog, others. Each conflict records the files, which side wins, and why. Targeted tests of modules touched by each merge are run niced. The pushed result is docs/ops/MERGE-PLAN-1031.md on bot/mvp-merge-plan-1031. Branches whose tips are ancestors of origin/bot/mvp-integrate-1031 are listed as safe to delete later. Nothing is deleted. Nothing is merged to main.
1 Goal met:          the plan doc is pushed, contained branches are listed, conflicts are recorded, and the handoff is pushed. Evaluator: the plan file plus the scratch merge log under tmp/merge-scratch (not pushed).
2 Turn cap:          not a fixed iteration count. Stop when the wall cap or the no-progress exit fires. Merge attempts on one branch: 2, then skip that branch and record it.
3 Budget cap:        cloud Grok only. No local model. No --local. No spend beyond this session.
4 Wall clock:        8 hours from 2026-11-01T00:36:11Z, so stop new items at 2026-11-01T08:16:11Z (20 minute handoff buffer). Hard stop 2026-11-01T08:36:11Z. Also stop at 2026-11-02T02:00:00Z if that is sooner (it is not).
5 No progress:       the same failure twice with no new information, or 3 items in a row skipped.
6 Human interrupt:   user stop. No questions. Conservative decision, one line in the decisions file, keep going.
7 Error threshold:   same as exit 5 (same failure twice, or 3 skips in a row).
8 External event:    a branch tip already contained in origin/bot/mvp-integrate-1031 is not merged again. A branch already merged to origin/main (ahead 0) is recorded and skipped. Red tests on the incoming tree before this lane's resolution: record and skip that area. Do not stop the run for a red base.
Loop type:           goal, with a wall-clock cap
Human gate:          no merge to main, no PR, no tag, no force push. Pregate plus Reviewer for this docs-only plan. Pregate is not run (see decisions).
```

Operator exits (same card, checked before every item):

1. Wall cap: 8 hours from launch, or Sunday 2026-11-01 18:00 PT (PST, 2026-11-02T02:00:00Z), whichever comes first. Leave 20 minutes to write the handoff.
2. Lane empty: no item left that fits the lane and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores (64) for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail on the incoming tree before this lane's resolution. Record them and skip that area. Do not stop the run.

## Plan

Overview: Count every 1031 bot branch plus mvp3-review-retry and backlog-catalog-1030 against origin/main, prove which tips already sit inside origin/bot/mvp-integrate-1031, then test-merge the rest onto a detached scratch stack in tmp/merge-scratch. Record conflict resolutions in docs/ops/MERGE-PLAN-1031.md. Run niced targeted tests after each merge that changes code. Push only this lane's branch. Do not merge to main.

Phases:
- inventory | read-only `git rev-list` and `git merge-tree` against origin | ahead/behind table, ancestor-of-integrate bit, conflict file names | none | lead
- stack-integrate | `tmp/merge-scratch` only | fast-forward origin/bot/mvp-integrate-1031 onto origin/main, then merge origin/bot/mvp-intfix-1031. Tests: the `tests/test_*.py` modules that differ from origin/main | inventory | lead
- stack-mvp3 | scratch stack | merge origin/bot/mvp3-review-retry, then origin/bot/mvp3-followups-1031. Conflicts resolved in scratch only. Tests: modules touched by the merge diff | stack-integrate | lead
- stack-backlog | scratch stack | merge origin/bot/backlog-catalog-1030. Tests: modules touched by that merge | stack-mvp3 | lead
- stack-others | scratch stack | remaining non-contained `*-1031` branches in alphabetical order, skipping this lane. Tests after each merge that changes code | stack-backlog | lead
- plan-doc | `docs/ops/MERGE-PLAN-1031.md`, this log, the decisions file, the handoff | plan pushed on bot/mvp-merge-plan-1031. Scratch merges are not pushed | stack-others | lead
- handoff | `docs/ops/HANDOFF-mvp-merge-plan-1031.md`, this log | SHAs, skips, evidence, fail/recover, gate, next step, final `state:` line | plan-doc | lead

Risks:
- Integrate changes 51 test modules versus main. Mitigation: run those modules niced in the scratch tree, one batch, no full discover, no docker, no local model. A red module is recorded and that area is skipped.
- Shared host. Mitigation: no flock job, no pregate, no `unittest discover`, no `make eval-*`. Targeted `nice -n 19 python3 -m unittest` only.
- Conflict policy applied in scratch can drop a hunk. Mitigation: every conflict file names the winner and the reason in the plan. Shared files (TODO.md, scripts, tests) keep fail-closed behavior from both sides when the hunks can be combined. A true line clash on shared code prefers the side whose tests still pass. Lane-owned handoff files come from the incoming lane.
- Other lanes own their branches and checkouts. Mitigation: this lane never checks out those branches in their worktrees. The scratch worktree is detached under this lane's `tmp/`. No push except `bot/mvp-merge-plan-1031`.

## Host at plan time (2026-11-01T00:36:11Z)

- MemAvailable: 74315768 kB (about 70.9 GiB). Floor is 16 GiB. Not pressured.
- Load: 3.21, 3.36, 3.82. Cores: 32. Threshold: 64. Not pressured.
- GitHub runner worker: not running. Pregate still not run: the drop-in forbids `scripts/pregate.sh`.

## Inventory (read-only, before the first scratch merge)

`git rev-list --left-right --count origin/main...branch` is behind then ahead. `anc` is yes when the tip is an ancestor of `origin/bot/mvp-integrate-1031` (safe to delete later, not deleted). `miss` is how many commits in `origin/main..branch` are not in integrate.

Integration tip: `1dee0b9` 2026-10-31 17:29:55 -0700 docs: stamp the pass 3 integrate handoff. It is 0 behind and 522 ahead of origin/main, so the first merge is a fast-forward.

Contained in integration (anc=yes), excluding the integration branch itself:

| branch | behind | ahead | files vs main |
| --- | ---: | ---: | ---: |
| origin/bot/mvp-backlog-burn-1031 | 0 | 247 | 310 |
| origin/bot/mvp-ci-cover-1031 | 0 | 231 | 296 |
| origin/bot/mvp-cloud-1031 | 12 | 17 | 8 |
| origin/bot/mvp-dogfood-1031 | 12 | 35 | 57 |
| origin/bot/mvp-dogfood-fix-1031 | 0 | 241 | 295 |
| origin/bot/mvp-eval-1031 | 12 | 12 | 10 |
| origin/bot/mvp-followups-fix2-1031 | 0 | 21 | 29 |
| origin/bot/mvp-mutate-preflight-1031 | 0 | 237 | 301 |
| origin/bot/mvp-preflight-1031 | 12 | 5 | 6 |
| origin/bot/mvp-realfail-1031 | 12 | 33 | 74 |
| origin/bot/mvp-realfail3-1031 | 0 | 240 | 347 |
| origin/bot/mvp-review-fix-1031 | 12 | 16 | 34 |
| origin/bot/mvp-review-fix2-1031 | 12 | 49 | 43 |
| origin/bot/mvp-selfhost-1031 | 12 | 61 | 52 |
| origin/bot/mvp-sixtask-1031 | 12 | 65 | 92 |
| origin/bot/mvp-sixtask-int-1031 | 0 | 258 | 347 |
| origin/bot/mvp-surface-1031 | 12 | 5 | 7 |

Not contained, and the merge-tree against integrate. Clean means git can merge with no conflict markers. Conflict lines are the files merge-tree reported.

| branch | behind | ahead | miss | vs integrate |
| --- | ---: | ---: | ---: | --- |
| origin/bot/mvp-intfix-1031 | 2 | 92 | 1 | clean (handoff docs only, commit 1c64e50) |
| origin/bot/mvp3-review-retry | 0 | 50 | 32 | CONFLICT docs/TODO.md, scripts/pfy_build_local.py, tests/test_pfy_build_local.py |
| origin/bot/mvp3-followups-1031 | 0 | 43 | 25 | ancestor of mvp3-review-retry. Same TODO and pfy_build_local conflicts if merged alone |
| origin/bot/backlog-catalog-1030 | 0 | 18 | 2 | CONFLICT docs/modules/pfylib.md |
| origin/bot/mvp-cloud-perf-1031 | 0 | 467 | 7 | clean |
| origin/bot/mvp-cloudfix-1031 | 0 | 252 | 2 | clean |
| origin/bot/mvp-crosslane-1031 | 0 | 335 | 16 | clean |
| origin/bot/mvp-daily-card-1031 | 2 | 92 | 4 | clean |
| origin/bot/mvp-docs-1031 | 2 | 98 | 9 | clean |
| origin/bot/mvp-docs-final-1031 | 0 | 526 | 7 | clean |
| origin/bot/mvp-dogfood2-1031 | 0 | 277 | 27 | CONFLICT six x-intake smoke scripts plus tests/test_mvp2_t3_daemon_stop.py (add/add) |
| origin/bot/mvp-dogfood3-1031 | 0 | 523 | 1 | clean |
| origin/bot/mvp-dsv4-1031 | 0 | 22 | 4 | CONFLICT docs/TODO.md |
| origin/bot/mvp-freshclone-1031 | 0 | 232 | 5 | clean |
| origin/bot/mvp-gom-dogfood-1031 | 0 | 252 | 3 | clean |
| origin/bot/mvp-local-t5-1031 | 0 | 237 | 10 | clean |
| origin/bot/mvp-merge-plan-1031 | 0 | 1 | 1 | this lane. Not merged onto the stack |
| origin/bot/mvp-mutate-cloud-1031 | 12 | 63 | 6 | clean |
| origin/bot/mvp-mutate-cloud2-1031 | 0 | 469 | 9 | clean |
| origin/bot/mvp-mutate-review-1031 | 12 | 44 | 11 | clean |
| origin/bot/mvp-pass3-review-1031 | 0 | 523 | 1 | clean |
| origin/bot/mvp-plan-1031 | 12 | 4 | 4 | CONFLICT add/add docs/build-dropins/mvp-integrate-1031.md |
| origin/bot/mvp-probe-fix2-1031 | 0 | 51 | 33 | ancestor of nothing in integrate. Contains mvp3-review-retry. Same three conflicts as review-retry if merged alone |
| origin/bot/mvp-realfail2-1031 | 12 | 93 | 36 | clean |
| origin/bot/mvp-review-quality-1031 | 0 | 468 | 8 | clean |
| origin/bot/mvp-selfhost2-1031 | 0 | 241 | 12 | clean |
| origin/bot/mvp-timeoutfix-1031 | 0 | 536 | 16 | clean |
| origin/bot/mvp-tmpclean-1031 | 2 | 94 | 1 | clean |
| origin/bot/mvp-tmpclean2-1031 | 0 | 33 | 4 | clean |

Merge order used from here:

1. origin/bot/mvp-integrate-1031 (fast-forward)
2. origin/bot/mvp-intfix-1031 (integration family, one handoff commit)
3. origin/bot/mvp3-review-retry, then origin/bot/mvp3-followups-1031
4. origin/bot/backlog-catalog-1030
5. The not-contained others, alphabetical, skipping this lane. Contained branches are not merged again.

## Items

Scratch SHAs below are not pushed. The plan doc commit is on this branch.

- integrate fast-forward | 1dee0b9 | tmp/integrate-tests.log 477 tests 502.110s | OK skipped=1
- mvp3 cherry-pick | 49ee477 | tmp/mvp3-tests.log 104 tests | FAILED 2, fixed before later merges
- intfix cherry-pick | 215be32 | docs only | handoff matches 1c64e50
- backlog pfylib.md ours | de91424 | docs only | recorded
- crosslane HEAD wins | 61f0b3e | later local and cloud suites | recorded
- docs-final QUICKSTART theirs plus walkthrough line | 2602fad | tmp/cloud-docs-tests.log 76 tests (pre-timeoutfix) | OK
- dogfood2 union | 90ac258 | tmp/dogfood2-review-tests.log at b8d9b64, 90 tests 144.915s | OK
- review timeout and warnings key | b8d9b64 | same 90-test log | OK
- dsv4 TODO ours | e6baeca | test_catalog_entry_numbers inside the 289 | passed
- cloud2 harness superset | 276063e | anchor tests red, see plan | fail-closed, not regenerated
- plan-1031 add/add keep HEAD addenda | cf5e0ef | docs only | recorded
- probe-fix2 cherry-picks including hardlink | d7b3914 | test_pfy_build_local and test_pfy_build_local_review inside the 289 at 9b63b93 | passed
- timeoutfix union, both recheck tests | 3ccc204 | test_pfy_build_cloud inside the 289 at 9b63b93 | passed
- stacked batch | 9b63b93 | tmp/stack-final-tests.log 289 tests 301.767s plus local-t5 12 tests | 281 passed, 8 failed; local-t5 OK
- expectation fix for recheck git and stricter help | 52e3ddc | tmp/stack-rerun-tests.log at 2275c47, 8 tests 4.355s | OK
- late retips dogfood3 selfhost2 cloud-perf | cee9bdd | tmp/stack-late-tests.log 3 tests 0.346s | OK
- plan doc | this branch | docs only, no product tests | see MERGE-PLAN-1031.md

Four tests stay red on the stacked runner (mutant anchors and one planted diff). Recorded in the plan. Not regenerated.

Host at freeze: MemAvailable about 68 GiB, load about 3.5, 32 cores. Not pressured.
Pregate not run: drop-in forbids scripts/pregate.sh.

state: lane empty | scratch cee9bdd92bce33df5a8c94c5c77eb376bc242dcd at 2026-11-01T01:20:48Z | plan doc is this commit | pregate not run | four anchor tests stay red on the stacked runner until they are re-cut

