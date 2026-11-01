# RUN LOG mvp-pregate-fixture-tmp-1031

Launch: 2026-11-01T04:37:41Z
Wall cap: 2026-11-01T07:37:41Z (3h from launch) or 2026-11-02T02:00Z, whichever comes first.
Handoff buffer: stop item work by 2026-11-01T07:17:41Z.
Base: origin/main 2a74482
Branch: bot/mvp-pregate-fixture-tmp-1031
Worktree: /home/mark/DEVELOP/pfy-mentat/tmp/mvp-pregate-fixture-tmp-1031
Host at launch: MemAvailable 66379140 KiB, load 3.00, 32 cores. Under the pressure line.
G0 at launch: Runner.Worker pid 2466766. No uv, ./pfy, or python test suite until that process name is gone.

LOOP EXIT CARD
Goal (success criteria): pregate test runs persist and prune only under an absolute PREGATE_RUNS_DIR. The shared main-checkout tmp/pregate-runs gains no new run folder from this suite, a planted run there survives PREGATE_KEEP_RUNS=1, and an empty or relative override exits 2 without writing.
1 Goal met: nice -n 19 python3 -m unittest tests.test_workflow_image_pin is green, and the red-on-base proof for the new assertions is recorded in this log.
2 Turn cap: 8 iterations on this single item.
3 Budget cap: cloud Grok only. No local model. No extra items. No full discover, eval, or docker.
4 Wall clock: 2026-11-01T07:37:41Z or 2026-11-02T02:00Z. Leave 20 minutes for the handoff.
5 No-progress: the same failure twice with no new information, or 3 items skipped. Hash is the unittest summary plus the first error line.
6 Human interrupt: user stop. Do not ask questions. Decisions go in the decisions file.
7 Error threshold: 3 consecutive failures of the same command, then stop.
8 External event: n/a. Do not merge. Do not open a PR.
Loop type: goal
Human gate: do not merge. After this lane the gate is pregate plus Reviewer. The operator runs real pregates.

Overview: One item. Tests call the real pregate.sh, which persists and prunes $MAIN_ROOT/tmp/pregate-runs and can delete operator summaries. Add PREGATE_RUNS_DIR, point every test call at a worktree temp dir, and prove the shared root is left alone.

Phases:
- exits | docs/ops/RUN-LOG-mvp-pregate-fixture-tmp-1031.md | exit card written before the edit | none | lead
- red-tests | tests/test_workflow_image_pin.py | new assertions fail on unmodified scripts/pregate.sh; shared runs dir restored | exits | lead
- fix | scripts/pregate.sh, docs/ops/PREGATE.md, tests/test_workflow_image_pin.py | targeted unittest green; shared runs dir unchanged across the run | red-tests | lead
- handoff | docs/ops/HANDOFF-mvp-pregate-fixture-tmp-1031.md, this log | state line, commit, push | fix | lead

Risks:
- A red proof with PREGATE_KEEP_RUNS=1 on the unfixed script deletes real run folders (21 were present at launch, keep default is 20). Mitigation: copy the shared runs dir and pregate-latest-summary.md into this worktree tmp/ and restore before doing anything else.
- G0 shares ~/.cache/uv. Mitigation: poll with pgrep -x until the worker is gone before any unittest or ./pfy.
- bot/mvp-flake-harness2-1031 and bot/flake-pgrep-x-1031 edit the top of scripts/pregate.sh. Mitigation: one new header line, plus the PERSIST and retention RUNS_DIR lines only.

state: plan written | tests: none yet | files: 0 | err: runner busy, tests held

item red-proof (a) | uncommitted | tests.test_workflow_image_pin.WorkflowImagePinTests.test_pregate_lint_calls_helper on unfixed scripts/pregate.sh | FAIL in 6.160s. New shared folder 7fe27b5-20261101T044958Z-2605344. Summary path was the main checkout runs root. Retention also removed 1dee0b9-20261101T021617Z-1497598. Both were restored from tmp/pregate-shared-backup. Live names match the backup (21). latest summary cmp matched. Stopped before (b) because Runner.Worker returned and another lane is queued to run scripts/pregate.sh 663ca169 under the heavy lock.

item red-proof (b)(c) | uncommitted | planted keep-1 and bad PREGATE_RUNS_DIR, unfixed script, user mount namespace | FAIL. (b) marker missing (planted run deleted). (c) empty, relative, and whitespace exited 0 not 2. REAL_RUNS_UNCHANGED. REAL_LATEST_UNCHANGED. 24.783s for the two tests.

item isolate-pregate-runs | c3ad923 | nice -n 19 python3 -m unittest tests.test_workflow_image_pin | PASS. Ran 17 tests in 12.707s, OK. REAL_RUNS_UNCHANGED (21). Lint-only overwrite of pregate-latest-summary.md restored from the pre-run copy.

state: DONE | tests: nice -n 19 python3 -m unittest tests.test_workflow_image_pin OK (17) | files: scripts/pregate.sh tests/test_workflow_image_pin.py docs/ops/PREGATE.md | err: none

LOOP REPORT
Type: goal
Goal: test pregates persist and prune only under an absolute PREGATE_RUNS_DIR
Exit fired: 1 Goal met. Lane empty. No second item.
Iterations: 2 (red proof, then fix; one test-mtime correction inside the fix)
Progress: green 17 tests, shared runs names unchanged
Evidence: c3ad923. Red lines above. Green log showed OK and REAL_RUNS_UNCHANGED.
Human gate: pending. Pregate plus Reviewer. Do not merge from this lane.
Next: operator pregate on c3ad923, then Reviewer. Thread PREGATE_RUNS_DIR through the flake branches' remaining pregate calls at merge.
Status: DONE
