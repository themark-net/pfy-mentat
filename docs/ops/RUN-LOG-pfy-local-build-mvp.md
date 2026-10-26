# RUN LOG: pfy-local-build MVP step 1

Headless `./pfy build --local` on branch `bot/mvp-local-build`.

- Start: 2026-10-26T06:38:08Z
- Clock cap: no new item after 4h (10:38Z). Stop by about 5h (11:38Z).
- HEAD at start: `6693b1fd08fba26249beedab8d56770b65b76aa2`
- Base: `origin/main` `7b716e86d5a3df3281b262ac15ec0b254f448041`
- Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-local-build`
- STOP file: absent at start

## Plan

Overview: Add a headless local-model build that turns one task into a tested branch in a tmp worktree, plus an offline coding eval and, if the host is quiet, one live `qwen3.6:35b` run. No PR, no merge, no cloud model.

Phases:

- item 1 local build | `scripts/pfy`, `scripts/pfy_build_local.py`, `tests/test_pfy_build_local.py`, `.gitignore` | `./pfy build --local` behavior tests green, cloud `./pfy build --help` and dry-run unchanged aside from the receipt stamp | none | lead (shared CLI)
- item 2 eval | `eval/local-build/`, `scripts/pfy_local_build_eval.py`, `scripts/pfy`, tests | fixture self-check and stub runner tests green | item 1 | lead
- item 3 live | `docs/ops/` only for the committed summary | gates logged, eval numbers or a named BLOCKED | items 1 and 2 | lead
- item 4 handoff | `docs/ops/HANDOFF-pfy-local-build-mvp.md`, this log, `docs/build-dropins/README.md`, `docs/TODO.md` if it fits | final checks, push `HEAD:bot/mvp-local-build` | items 1 to 3 | lead

Risks:

- Swap on nimo was nearly full at start (SwapFree about 10 MB) while MemAvailable was about 65 GiB. Item 3 still has to clear 40 GiB of MemAvailable+SwapFree and must not unload a model this run did not load.
- A live load of `qwen3.6:35b` (about 22 GB) only happens in item 3, behind the memory guard.
- Baseline `python3 -m unittest discover -s tests -t .` is running. Known env flakes stay listed. New failures block the run.

## Decisions

- Lead implements in this worktree | per-phase git worktrees | the request forbids any other worktree, and items 1 and 2 share `scripts/pfy`
- Stamp uses UTC time plus microseconds | second resolution only | two tests in the same second must not share a worktree path
- Commit on detached HEAD, then create the branch ref | `git switch -c` before the commit | a failed commit must not leave a branch
- Positional task and `--prompt-file` together exit 2 | silent preference | do not drop text the operator passed
- `--unload-at-end` wins over `--keep-model` | the reverse | the eval's last task has to unload a model an earlier task loaded
- Create the worktree, then run `tests_before` on that clean tree | run the tests in the origin checkout | the tool must not edit the checkout it was started from
- A `:cloud` tag records reason `cloud-tag` | fold it into `model-too-big` | the 40 GB case and the cloud-tag case are different failures
- Size cap is 30 * 1024^3 bytes | 30 * 10^9 | the memory gates in this drop-in are GiB
- Commit email `pfy-local-build@localhost` | omit the email | git will not commit without one
- Model env is `PFY_LOCAL_BUILD_MODEL` only | also read `PFY_BOT_MODEL` | the drop-in names one env var
- `--keep-model` and `--unload-at-end` land in item 1 | wait for item 2 to edit the unloader | the process that owns unload has to grow the flags
- Agent and test children get a scrubbed env plus `PFY_LOCAL_BUILD_SCENARIO` and `PFY_STUB_*` when set | pass the full parent env | isolation tests require token, key, and secret names to be absent
- Do not pass opencode `--auto` | pass it so prompts cannot hang | the drop-in forbids approval-bypass flags
- Bash patterns `* /*`, `*>/*`, and `*..*` are deny, on top of `external_directory: deny` | `external_directory` alone | opencode 1.18.32 denies write/edit outside the git worktree, and it does not apply that rule to a shell redirect. The patterns block the redirect. `python3 -m unittest discover -s tests -t .` does not match them
- Child HOME may sit under the user home because the repo does | require `Path.home()` to be absent from parents | on nimo the worktree is under `/home/mark`, so the check is "HOME is not the real home directory"
- Eval refuses to start below 8 GiB (`SKIP: mem-guard`) | use the build's 32 GiB floor as the skip | 10 GiB must still enter task 1 and return BLOCKED. The build floor stays 32
- `reference.patch` is not copied into the task repo | copy the whole fixture | the agent must not apply the known-good patch
- A task passes only when the receipt says PASS and `check_cmd` exits 0 | trust the build process exit code | deleting a test can leave the test command at exit 0 while the receipt says `tests-regressed`

## Opencode check

2026-10-26. Binary `/home/mark/.local/bin/opencode` version 1.18.32.

`opencode run --help` lists `--pure`, `--model`, `--variant`, and `--auto` (default false). This runner does not pass `--auto`.

One-line run against a loopback stub (no real model), cwd a fresh git repo under `$W/tmp/scratch/opencode-probe/wt`, config from `_write_config`, stdin closed, 40s cap. The stub returned tool calls. Result, no permission prompt and no hang:

- `write` of an absolute path inside the worktree: completed, `hello.txt` created
- `bash` `printf ... > inside.txt`: completed
- `write` of a path outside the worktree: status error, `external_directory` deny, file not created
- `bash` redirect to an absolute path outside the worktree: status error, bash pattern `* /*`, file not created
- process exit 0

Tools the binary advertised: bash, edit, glob, grep, read, skill, task, todowrite, write. `write` and `edit` require an absolute `filePath`.

## Baseline

`python3 -m unittest discover -s tests -t .` with `TMPDIR=$W/tmp/scratch`, before this slice's tests existed.

Ran 804 tests in 465.571s. FAILED (failures=1, skipped=16), exit 1.

The one failure is `tests.test_local_bench.OutdirPathTests.test_relative_outdir_log_path_safe`. `TMPDIR` was inside that package's root, so a temp dir the test treats as out-of-tree was in-tree. Environmental. Not fixed here. No other failure at that base.

## RED

Each mutant was applied, the named test failed, and the source was restored. Nothing mutated was committed.

- RED: skip the free-RAM-plus-swap check -> test_low_memory_blocks_and_full_swap_is_not_free
- RED: count total swap -> test_low_memory_blocks_and_full_swap_is_not_free
- RED: skip the protected-path check -> test_protected_test_edit_does_not_commit
- RED: accept a lower test count -> test_deleting_a_test_is_a_regression
- RED: unload unconditionally -> test_model_already_loaded_is_not_unloaded
- RED: skip start_new_session -> test_hang_is_timeout_and_the_group_is_gone (orphan stub still alive after the runner; reaped)
- RED: commit before the gate -> test_protected_test_edit_does_not_commit, test_worse_tests_do_not_commit, test_deleting_a_test_is_a_regression
- RED: run in the origin checkout instead of a worktree -> test_fix_creates_one_commit_and_leaves_the_checkout_alone

## Items

- item 1: DONE. Commit `b63d8d011ebe95558c35101c2f62d1a23975f861` (`pfy-local-build: item 1 headless local build`). Behavior suite `tests.test_pfy_build_local`: 25 tests OK. Pushed to `origin/bot/mvp-local-build`.
- item 2: DONE. Commit `fbbaf90bc5a245d5ca69f274b610c68f369f3664` (`pfy-local-build: item 2 coding eval fixture and runner`). `eval/local-build/` (8 fixtures) and `scripts/pfy_local_build_eval.py` (`./pfy eval-local-build`). `tests.test_pfy_local_build_eval`: 13 tests OK. Pushed to `origin/bot/mvp-local-build`.

### Item 2 RED

- RED: reference.patch for t01 is a no-op -> test_every_fixture_fails_before_the_patch_and_passes_after
- RED: count a SKIP or BLOCKED as PASS -> test_missing_opencode_skips, test_low_memory_blocks_the_first_task_and_stops
- RED: read the pass rate from the stub exit code instead of the receipts -> test_delete_tests_is_zero_and_the_reason_comes_from_the_receipt
- RED: run check_cmd against the fixture instead of the produced worktree -> test_solve_mode_passes_all_eight

- item 3: IN PROGRESS. Gate re-check 2026-10-26T07:28:01Z (earlier snapshot 2026-10-26T07:26:15Z also passed). STOP absent. `ollama ps` header only (no loaded model). `ps -eo comm` llama-server count 0. Only ollama process is pid 4879 `/usr/local/bin/ollama serve`. MemTotal 112641192 kB, MemAvailable 66283992 kB (63.213 GiB), SwapFree 44484 kB (0.042 GiB), sum 63.256 GiB, need 40 GiB (22 GB model plus KV plus margin), headroom 23.256 GiB, gate PASS. `qwen3.6:35b` listed at 22621314381 bytes (21.07 GiB), under the 30 GiB cap. opencode 1.18.32.
- item 3 live start: 2026-10-26T07:29:40Z, `timeout 90m python3 -u scripts/pfy_local_build_eval.py --model qwen3.6:35b --require-live`, shell pid 2815674. `free -g` at start: Mem available 63, Swap used 7 of 8. While loaded (2026-10-26T07:30:27Z): `ollama ps` shows `qwen3.6:35b` id `a7eb95c53bcf`, 23 GB, 100% GPU, CONTEXT 262144. 262144 is above 16384, so no `context_warning` and Ollama was not reconfigured. First task is `t01-fix-off-by-one`. Stamp `20261026T072940388555Z`. Result not in yet.
- item 4: pending
