# Handoff mvp-pregate-fixture-tmp-1031

Lane empty. One item. Branch `bot/mvp-pregate-fixture-tmp-1031`. Do not merge from this lane.

## Done

| Item | SHA | Result |
|---|---|---|
| Isolate pregate test runs from the shared runs root | `c3ad923` | Pushed. `nice -n 19 python3 -m unittest tests.test_workflow_image_pin`: Ran 17 tests in 12.707s, OK. Shared `tmp/pregate-runs` name list unchanged (21 folders). |

Files: `scripts/pregate.sh`, `tests/test_workflow_image_pin.py`, `docs/ops/PREGATE.md`.

`PREGATE_RUNS_DIR`, when set, is the persist directory and the only directory retention prunes. Unset still uses `$MAIN_ROOT/tmp/pregate-runs`. An empty, relative, or whitespace value exits 2 before any run folder is created. The image-pin tests set `PREGATE_RUNS_DIR` and `TMPDIR` to a `tempfile.mkdtemp` directory under this worktree's `tmp/`, and they read the summary from there.

No other test under `tests/` calls `scripts/pregate.sh`.

## Skipped

None. Lane empty after this item. No open question needed an ADR.

## Red on the unfixed script

- (a) `test_pregate_lint_calls_helper` FAIL in 6.160s. New shared folder `7fe27b5-20261101T044958Z-2605344`. Summary path was the main checkout runs root. Retention also removed `1dee0b9-20261101T021617Z-1497598`. Both were restored from a copy under this worktree's `tmp/`. Names matched again (21). Latest summary matched.
- (b) `test_planted_shared_run_survives_keep_one` FAIL. `marker.is_file()` was false: keep-1 deleted planted `deadbee-...`. Ran inside a user mount namespace so the real runs directory was not the prune target. `REAL_RUNS_UNCHANGED`.
- (c) `test_bad_runs_dir_exits_2_and_writes_nothing` FAIL for empty, relative, and whitespace. Exit code was 0, not 2, and lint reported PASS. Same namespace. `REAL_RUNS_UNCHANGED`. `REAL_LATEST_UNCHANGED`.

The first green run then failed one assertion: `write_text` refreshed the planted directory mtime, so the "new folder" check saw the plant itself. Stamp is applied after the write. Re-run was the 17-test OK above. That re-run did not weaken the red proof. The unfixed script had already deleted the marker.

## How it fails and how it recovers

Fail: a test pregate writes `$MAIN_ROOT/tmp/pregate-runs/<run-id>` and prunes that directory to `PREGATE_KEEP_RUNS`. With 21 real folders and the default keep of 20, one operator summary disappears per run. With keep 1, every older run-id folder goes, which is what made the 1dee0b9 integration pregate look failed on 2026-10-31. A bad `PREGATE_RUNS_DIR` used to be ignored, so the same write still happened.

Recover: tests pass an absolute `PREGATE_RUNS_DIR`. Retention's `find` starts there, and `rm` runs only when the path is `$RUNS_DIR/*` and is not the current run. An empty, relative, or whitespace override exits 2 before `mkdir`, so the shared runs root, `tmp/pgs`, and `tmp/pg` stay as they were.

The convenience copy `tmp/pregate-latest-summary.md` is still on the main checkout. The green suite overwrote it with a lint-only summary (`pass=1`). This lane copied the previous file back. Moving that pointer was left out so the script diff stays on the persist and retention lines.

## Cross-lane

- `bot/mvp-flake-harness2-1031` and `bot/flake-pgrep-x-1031` edit the top of `scripts/pregate.sh` (runner gate, exit 3) and do not change `PERSIST`. This lane added one header line after the keep-runs comment, set `RUNS_DIR` just after `MAIN_ROOT` is known, and stopped reassigning `RUNS_DIR` at the retention find. Do not take their runner-gate hunk from this branch. It is not here.
- Those branches also rewrite `tests/test_workflow_image_pin.py`. After a merge, every remaining `scripts/pregate.sh` call (`run_pregate_lint`, the venv pregate call, and `test_failing_image_pin_lint_fails_pregate`) still needs `PREGATE_RUNS_DIR` and `TMPDIR` on a per-test directory under the worktree `tmp/`. Their `test_pregate_lint_calls_helper` stopped calling the script. Keep that, and keep the isolation on the calls that remain.
- Their `docs/ops/PREGATE.md` edits are the exit-code sentence (exit 3) and the lint table row. This lane edited the knobs sentence, the run-folder bullet, and the retention bullet.
- While this lane waited, another process was queued to run `scripts/pregate.sh 663ca169ea14d139ada423f9495d33ed86a03483` under `tmp/heavy-1030.lock`. This lane did not signal it and did not run a real-ref pregate outside the tests.

## Gate

Pregate plus Reviewer. This change is a script plus tests. This lane did not run `scripts/pregate.sh` against a real ref outside `tests.test_workflow_image_pin`.

## Next

Operator runs pregate on `c3ad923` (or on the handoff commit that follows it, which is docs only) and sends the summary to Reviewer. On merge with the flake branches, thread `PREGATE_RUNS_DIR` through their remaining pregate calls.
