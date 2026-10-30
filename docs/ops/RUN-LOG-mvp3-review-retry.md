# RUN-LOG mvp3-review-retry

Started: 2026-10-30 (this session, UTC clock in the phase lines).
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/mvp3`
Branch: `bot/mvp3-review-retry` (tracks `origin/bot/mvp3-review-retry`)
Head at start: `c9650e2` (docs drop-in on top of `bot/mvp2-report` `85c53dc`, which is `origin/main` `1e99251` plus the MVP-2 report).
Model for Part 2 only: `qwen3.6:35b` via Ollama. No cloud arm. No second model.

## Exits (check before every arm)

1. Done: all 6 tasks have a final local result (PASS-accepted, PASS-rejected, FAIL, BLOCKED or TIMEOUT) and the report is pushed.
2. Wall cap: 3 hours from the start of the first model call. At the cap, finish the current attempt only if it ends within 10 minutes, otherwise kill its process group. Record what remains as `not-run (wall cap)`, write the report with partial numbers and push.
3. Memory or lockup: stop if `MemAvailable+SwapFree` drops below the 32 GiB floor, if any arm's process group outlives its timeout by more than 60 s, if `ollama ps` is unreadable twice in a row, if the Ollama API stops answering for 120 s, or if the host load average stays above 2x core count (64) for 5 minutes. Kill only process groups this run started, unload the model, record `STOPPED <reason>` in this log and the report, push, exit.
4. No progress: if two consecutive tasks end BLOCKED for the same infrastructure reason, stop and report it.
5. Red base: if `python3 -m unittest discover -s tests -t .` with bwrap hidden fails on the base before any product change, record the failure and stop. Do not fix unrelated code.

## Plan

Overview: Add a review-and-retry loop to `./pfy build --local` (deterministic scope, size, and wiring checks, then one local-model review, at most 3 attempts), prove it with stub-agent behavior tests, then re-run the six MVP-2 tasks locally at base `997d89264495861a178713ccf7d4447ea828afc4` and compare with the MVP-2 numbers.

Phases:
- red-base | (no product edits) | `python3 -m unittest discover -s tests -t .` with bwrap hidden, TMPDIR under this worktree `tmp/` | none | lead
- review-loop | `scripts/pfy_build_local.py`, `tests/test_pfy_build_local.py`, `tests/test_pfy_build_local_review.py` | new review tests green; existing local-build tests still green | red-base | lead
- trial-harness | `eval/mvp3/` | task copies, `run_trial.py`, `prove-red` prints PROVE_DONE ok | review-loop | lead
- suite-push | same | full discover with bwrap hidden recorded; commit; push `bot/mvp3-review-retry` | review-loop | lead
- trials | `eval/mvp3/results`, `eval/mvp3/patches` | six local results or a recorded STOPPED | suite-push | lead
- handoff | `eval/mvp3/REPORT.md`, `docs/ops/HANDOFF-mvp3-review-retry.md`, `docs/TODO.md` | report compares MVP-3 local with MVP-2 local and cloud; push | trials | lead

Risks:
- Reviewer too strict, so real tasks end PASS-REJECTED. Mitigation: receipts name the check; `--no-review` is the recovery; the report says which check fired.
- Default review-on changes MVP-1 green runs. Mitigation: with no `files:` list the scope check is skipped; size defaults are 3 files and 250 lines; the test stub accepts a well-formed review so existing PASS tests stay one attempt.
- Baseline suite races a half-written runner. Mitigation: do not edit `scripts/pfy_build_local.py` until the red-base process has exited.
- Trial loads a second model or drops under 32 GiB. Mitigation: same guards as MVP-2; unload between tasks; stop on the memory exit.
- Pregate's scratch lives under the main checkout (`git-common-dir` parent). Mitigation: run the same discover here with bwrap removed from PATH. Do not create a worktree under `~/DEVELOP/pfy-mentat`.

## Phases

### red-base

First discover, bwrap hidden, TMPDIR inside this worktree (`tmp/suite-base/tmp`): Ran 948 tests in 440.245s, FAILED (failures=1, skipped=100). The only failure is `tests.test_local_bench.OutdirPathTests.test_relative_outdir_log_path_safe`. The temp dir sat inside the repo, so `log_path_for_receipt` returned a relative path. That is the known environmental failure from the MVP-1 run log, caused by this run's TMPDIR, not by a product regression. Log: `tmp/suite-base/unittest.log`.

Re-run with the same hidden bwrap PATH and TMPDIR `/home/mark/DEVELOP/pfy-mentat/tmp/pgs/mvp3-suite-base/tmp` (outside this worktree, the pregate scratch parent, gitignored). The new review test module was held aside at `tmp/test_pfy_build_local_review.py.pending` so this discover is the base suite. Log: `tmp/suite-base/unittest-rerun.log`.

Result: Ran 948 tests in 439.849s, OK (skipped=100), EXIT:0. The in-repo TMPDIR flake did not return. Base is green. Product edits may start.

state: DONE | tests: python3 -m unittest discover -s tests -t . (bwrap hidden, out-of-tree TMPDIR) Ran 948 OK skipped=100 in 439.849s | files: 0 | err: none

Review tests on that unchanged runner, before the loop existed: Ran 7 in 44.918s, FAILED (failures=5, errors=2). `--no-review` and `--retries` were unrecognized. A green out-of-scope patch was still a one-shot PASS. Log: `tmp/suite-base/review-red.log`.

### review-loop

The loop is in `scripts/pfy_build_local.py`. Flags are not plumbed through `pfylib/cli.py`. After the stub bind (sibling `stub-notes` directory), `python3 -m unittest tests.test_pfy_build_local_review -v` Ran 7 in 9.890s, OK. Log: `tmp/suite-base/review-green2.log`.

Existing module after the loop: `python3 -m unittest tests.test_pfy_build_local` Ran 61 in 80.625s, OK. Log: `tmp/suite-base/local-build-after.log`.

First full discover after the loop (bwrap hidden, out-of-tree TMPDIR): Ran 955 in 508.147s, FAILED (failures=3, skipped=100). All three were `tests.test_pfy_local_build_eval`. The eval HTTP stub returned `"noop"` for every chat completion. The reviewer treated that as `review-unparseable`, retried to 3, and scored PASS-REJECTED, so solve was 0/8. Log: `tmp/suite-base/unittest-final.log`.

The stub now returns `{"verdict":"accept","reasons":[]}` only when the body contains `pfy-review-v1`. Other chat stays `"noop"`. Eval module after that: Ran 16 in 45.354s, OK. Log: `tmp/suite-base/eval-after.log`.

Second full discover: Ran 955 in 501.228s, FAILED (failures=1, skipped=100). The only failure was `test_module_run_leaves_no_new_tmp_dirs` with extra path `/tmp/pfy-xintake-140-test-gwouai41`. That prefix comes from `tests/test_x_intake_smoke_140_142.py`, which is not in the cleanup module list and is not written by the local-build runner. Isolated re-run of that one test: Ran 1 in 51.975s, OK. Log: `tmp/suite-base/tmp-cleanup-rerun.log`. A GitHub actions-runner discover was in `/home/mark/actions-runner/_work/pfy-mentat/pfy-mentat` at the same time (pid 3753265). Left alone.

Third full discover, same hidden bwrap PATH, same TMPDIR: Ran 955 tests in 501.227s, OK (skipped=100), EXIT:0. Start 2026-10-30T17:40:26Z, end 2026-10-30T17:48:48Z. Log: `tmp/suite-base/unittest-final3.log`. Baseline was Ran 948 OK skipped=100 in 439.849s. The seven new tests account for 948 to 955.

state: DONE | tests: review 7 OK; local-build 61 OK; discover Ran 955 OK skipped=100 in 501.227s | files: runner + tests | err: none

### trial-harness

Task copies under `eval/mvp3/tasks/` differ from `eval/mvp2/tasks/` only by a `files:` line, plus a `require:` line on t5. `eval/mvp3/run_trial.py` is the local arm only.

`python3 eval/mvp3/run_trial.py prove-red` at 2026-10-30T17:49:46Z, before any model call. Host: MemAvailable about 72 GiB, SwapFree about 5 MB, load 2.75, `ollama ps` empty.

```
PROVE_RED t1-smolvm-stderr-first failed=1 errors=0
PROVE_RED t2-tree-sig-119 failed=1 errors=0
PROVE_RED t3-daemon-stop-fail failed=1 errors=0
PROVE_RED t4-timeout-substep failed=2 errors=0
PROVE_RED t5-receipts-outside-repo failed=1 errors=0
PROVE_RED t6-tree-sig-three failed=3 errors=0
PROVE_DONE ok
```

Log: `tmp/mvp3-runs/prove-red.stdout`. Worktrees removed after each gate.

state: DONE | tests: prove-red PROVE_DONE ok | files: eval/mvp3 | err: none

### suite-push

Full discover recorded above. Pushed `b25fc35` to `origin/bot/mvp3-review-retry` (c9650e2..b25fc35). No rebase, no force, no PR.

state: DONE | tests: discover Ran 955 OK skipped=100 in 501.227s | files: 13 | err: none

Host at the green suite: MemAvailable about 71 GiB, SwapFree about 5 MB, 32 cores, `ollama ps` empty, `qwen3.6:35b` present in tags and not loaded. Floor stays 32 GiB.
