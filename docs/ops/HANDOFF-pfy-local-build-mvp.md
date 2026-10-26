# Handoff: pfy-local-build MVP step 1

Branch `bot/mvp-local-build`. Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/mvp-local-build

This file is updated as the run goes. Item 4 fills the live result, the final SHA, and the one-line answer.

## What item 1 built

`./pfy build --local "<task>"` runs a local OpenCode agent in a new git worktree under `<repo>/tmp/`, gates on the test command, and on PASS commits one branch `local/<slug>-<stamp>`. It does not push, does not open a PR, and does not commit in the checkout it was started from.

Cloud `./pfy build` (`scripts/pfy_build_p.py`) is unchanged. `--local` anywhere in argv is the switch. The shell `exec`s the local runner so SIGTERM reaches Python.

## Usage

```text
./pfy build --local "<task>" [--repo DIR] [--base REF] [--model TAG]
    [--endpoint URL] [--test-cmd CMD] [--timeout SEC] [--test-timeout SEC]
    [--min-free-gb N] [--protect GLOB] [--receipt-dir DIR]
    [--keep-worktree] [--keep-model] [--unload-at-end]
    [--run-tests-on-timeout] [--dry-run]
./pfy build --local --prompt-file FILE [same flags]
```

Flag wins over env over default.

| Input | Env | Default |
|---|---|---|
| `--repo` |  | git repo containing the cwd |
| `--base` |  | `origin/main` if it exists, else `HEAD` |
| `--model` | `PFY_LOCAL_BUILD_MODEL` | `qwen3.6:35b` |
| `--endpoint` | `LOCAL_OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` |
| `--test-cmd` | `PFY_LOCAL_BUILD_TEST_CMD` | `python3 -m unittest discover -s tests -t .` |
| `--timeout` | `PFY_LOCAL_BUILD_TIMEOUT` | 1200 |
| `--test-timeout` |  | 600 |
| `--min-free-gb` | `PFY_LOCAL_BUILD_MIN_FREE_GB` | 32 |
| `--protect` |  | none, repeatable |
| `--receipt-dir` |  | `<repo>/pipelines/dogfood/build-local/<stamp>/` |

`--keep-model` skips unload unless `--unload-at-end` is also set. A single `./pfy build --local` unloads only a model that this run loaded. `--dry-run` runs the pre-flight checks, prints the plan, starts nothing, and loads nothing.

## Receipt schema `pfy-local-build/1`

File: `<receipt-dir>/receipt.json`, written atomically, including on BLOCKED (then `worktree` is null).

Fields: `schema`, `id`, `task` (first 500 chars, redacted), `repo`, `base_sha`, `model`, `endpoint` (host only), `status` (`PASS|FAIL|BLOCKED|TIMEOUT`), `reason`, `exit_code`, `wall_seconds`, `agent_seconds`, `tests_before`, `tests_after`, `files_changed`, `branch`, `commit`, `worktree`, `model_was_loaded`, `unloaded`, `mem` (`mem_available_gb`, `swap_free_gb`, `min_available_gb`), `opencode_version`, `agent_log`, `started_at`, `finished_at` (UTC, `Z`).

`tests_before` and `tests_after`: `cmd`, `exit`, `passed`, `failed`, `errors`, `seconds`, `tail` (last 40 lines, redacted).

Summary line: `PASS|FAIL|BLOCKED:|TIMEOUT <reason> branch=<name|none> receipt=<path>`.

Exit codes: 0 PASS or a clean dry-run, 1 FAIL, 2 usage or missing tool (`no-opencode`, `no-model`), 3 TIMEOUT, 4 BLOCKED (`mem`, `busy-host`, `model-too-big`, `cloud-tag`, `another run`).

## Guards, fail, recover

| Fail | Exit | Reason | Recover |
|---|---|---|---|
| `MemAvailable + SwapFree` below `--min-free-gb` | 4 | `mem` | free memory. Full swap counts as 0. `SwapTotal` is not free |
| another model loaded | 4 | `busy-host` | that model unloads on its own. This tool does not unload it |
| model size over 30 GiB | 4 | `model-too-big` | pick a smaller tag |
| tag contains `:cloud` | 4 | `cloud-tag` | pick a local tag |
| `opencode` missing | 2 | `no-opencode` | `./pfy attach opencode` |
| Ollama down or tag missing | 2 | `no-model` | start Ollama, or name a tag it lists |
| lock held by a live pid | 4 | `another run` | wait. A dead pid's lock does not block |
| agent edits nothing | 1 | `no-change` | a real edit |
| a `--protect` path changes | 1 | `protected-path-changed` | leave those paths alone |
| tests fail or get worse | 1 | `tests-failed` | fix the code |
| fewer tests than before, even if exit 0 | 1 | `tests-regressed` | do not delete tests |
| test command cannot start | 1 | `test-cmd-failed-to-start` | a command that exists |
| agent exceeds `--timeout` | 3 | `timeout` | longer timeout, or `--run-tests-on-timeout` to still run the gate. No commit by default |
| SIGINT or SIGTERM | 1 | `interrupted` | run again. The lock is released |
| watchdog sees MemAvailable under 16 GiB | 1 | `mem-edge` | free memory. Only this run's agent group is killed |

On FAIL, TIMEOUT, and BLOCKED there is no branch and no commit. The worktree is kept when one was created.

## Eval

```text
./pfy eval-local-build [--only ID] [--limit N] [--model TAG] [--endpoint URL]
    [--timeout SEC] [--test-timeout SEC] [--require-live]
```

Same command: `python3 scripts/pfy_local_build_eval.py`.

Fixtures live in `eval/local-build/fixtures/<id>/` with `tasks.json`. Each task fails its tests and its `check_cmd` before `reference.patch` and passes both after. The patch is not copied into the repo the agent sees.

The runner writes `pipelines/dogfood/build-local-eval/<stamp>/summary.json` and `summary.md` (gitignored). Exit 0 if it finished, including a low pass rate or a skip. Exit 1 if the runner broke. Exit 2 if `--require-live` and a skip fired.

Skips, printed as `SKIP: <reason>`: `opencode-missing`, `ollama-unreachable`, `model-missing <tag>`, `mem-guard <gib>`, `busy-host <model>`. A BLOCKED task stops the run. Later tasks are `not-run`. A skip or a BLOCKED task is not a pass.

Tasks stay on one model load: every build uses `--keep-model`, and the last build uses `--unload-at-end` only if this eval loaded the model. A model that was already loaded is left loaded.

## Live result

Stamp `20261026T072940388555Z` on host `nimo`, model `qwen3.6:35b`, endpoint `127.0.0.1:11434`. Eval exit 0. Pass rate 8/8 (1.0). Total 571.668 s. Mean 71.459 s. No failures. CONTEXT while loaded was 262144, so there is no `context_warning`. Ollama was not reconfigured.

| id | status | reason | wall_s |
|---|---|---|---|
| t01-fix-off-by-one | PASS | ok | 94.830 |
| t02-add-function | PASS | ok | 57.580 |
| t03-rename-symbol | PASS | ok | 78.778 |
| t04-fix-mutable-default | PASS | ok | 66.103 |
| t05-add-cli-flag | PASS | ok | 41.559 |
| t06-parse-duration | PASS | ok | 69.653 |
| t07-remove-dead-code | PASS | ok | 60.889 |
| t08-fix-unicode-strip | PASS | ok | 102.276 |

Each task had `tests_before.exit` 1 and `tests_after.exit` 0. The receipt for t08 has `unloaded: true`. At 2026-10-26T07:39:19Z `ollama ps` was empty, `opencode` comm count was 0, and `free -g` showed Mem available 86 (start was 63). Swap stayed full, which it already was at the gate.

Can `./pfy build --local` replace Grok Build on a build-only run today? For a tiny build-only fix, yes: this live eval passed 8/8 in 572s, and each task went from a failing test to a tested commit on `qwen3.6:35b`. A real task from `docs/TODO.md` is still unmeasured (MVP-2).

## Known gaps

- One model at a time. A second loaded model is `BLOCKED: busy-host`, and this tool does not unload it.
- The default test command is `python3 -m unittest discover -s tests -t .`. Other stacks need `--test-cmd`.
- If a host's Ollama context is below 16384, the runner records `context_warning` and does not reconfigure Ollama. This run's context was 262144.
- No push and no PR, by design. The branch stays in the repo's `tmp/` worktree.
- The live numbers are the 8 tiny fixtures. They are not a cost or pass-rate comparison against cloud `./pfy build`.

## RED

- RED: skip the free-RAM-plus-swap check -> test_low_memory_blocks_and_full_swap_is_not_free
- RED: count total swap -> test_low_memory_blocks_and_full_swap_is_not_free
- RED: skip the protected-path check -> test_protected_test_edit_does_not_commit
- RED: accept a lower test count -> test_deleting_a_test_is_a_regression
- RED: unload unconditionally -> test_model_already_loaded_is_not_unloaded
- RED: skip start_new_session -> test_hang_is_timeout_and_the_group_is_gone
- RED: commit before the gate -> test_protected_test_edit_does_not_commit, test_worse_tests_do_not_commit, test_deleting_a_test_is_a_regression
- RED: run in the origin checkout instead of a worktree -> test_fix_creates_one_commit_and_leaves_the_checkout_alone
- RED: reference.patch for t01 is a no-op -> test_every_fixture_fails_before_the_patch_and_passes_after
- RED: count a SKIP or BLOCKED as PASS -> test_missing_opencode_skips, test_low_memory_blocks_the_first_task_and_stops
- RED: read the pass rate from the stub exit code instead of the receipts -> test_delete_tests_is_zero_and_the_reason_comes_from_the_receipt
- RED: run check_cmd against the fixture instead of the produced worktree -> test_solve_mode_passes_all_eight

## Status

- Branch: `bot/mvp-local-build`
- Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/mvp-local-build
- Base: `7b716e86d5a3df3281b262ac15ec0b254f448041`
- item 1: DONE. `b63d8d011ebe95558c35101c2f62d1a23975f861`. 25 behavior tests.
- item 2: DONE. `fbbaf90bc5a245d5ca69f274b610c68f369f3664`. 13 behavior tests.
- item 3: DONE. `da2ce97`. Live 8/8, 571.668 s. CONTEXT 262144. No `context_warning`.
- item 4: this handoff.
- Baseline unit suite, before these tests: Ran 804 tests, failures=1, skipped=16. The one failure is `tests.test_local_bench.OutdirPathTests.test_relative_outdir_log_path_safe` when `TMPDIR` sits inside the repo. Environmental. Not fixed here.
- Final unit count: direct `python3 -m unittest discover -s tests -t .` at 2026-10-26T07:59:48Z: Ran 842 tests in 531.297s, FAILED (failures=1, skipped=16). The only failure is the same `test_relative_outdir_log_path_safe` (the out-of-tree log path was relativized because `TMPDIR` is inside the repo). The structural gate's earlier run was Ran 842 in 548.285s with that same single failure. 842 is the baseline 804 plus 25 item-1 tests plus 13 item-2 tests. 0 new failures.
- Local CI (2026-10-26, `TMPDIR` under this worktree's `tmp/scratch`): `run_structural.py` exit 1 because that same unittest failure fails the `pfylib_unittests` check. Every other `run:` step exited 0: golden, gab selftest, jev selftest, launch wizard, launcher filemode and `bash -n` and `py_compile` and `./pfy help`, encoded-payload selftest and check, catalog dashboard, catalog_check, smoke_contract_lint, jev cua-s1-forms smoke, toolset matrix, toolset plan, hedge. Regenerated `pipelines/eval/golden.latest.md` and `pipelines/catalog/dashboard.latest.md` are restored with `git checkout --` and are not part of this commit. `pipelines/eval/structural.latest.md` is gitignored.
- Exit: goal met (DONE). STOP file absent. No stop-file, 2-skips, time-cap, or red-base exit.
- Final head: the tip of `bot/mvp-local-build` whose subject is `pfy-local-build: item 4 handoff and index`. A commit cannot record its own SHA inside its tree. Read it with `git rev-parse HEAD` on that branch.

## Commits (`git log origin/main..HEAD --oneline`)

- (this commit) pfy-local-build: item 4 handoff and index
- da2ce97 pfy-local-build: item 3 live eval 8/8
- 1271089 docs: record live eval context 262144
- 0cc74c0 docs: record item 3 gate before live eval
- fbbaf90 pfy-local-build: item 2 coding eval fixture and runner
- b63d8d0 pfy-local-build: item 1 headless local build
- 6693b1f docs: pfy-local-build-mvp drop-in (MVP step 1, headless pfy build --local)
