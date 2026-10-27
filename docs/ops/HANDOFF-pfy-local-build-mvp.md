# Handoff: pfy-local-build MVP step 1, fix round 1

Branch `bot/mvp-local-build`. Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/mvp-local-build

Tester and Reviewer failed `e63a95b2`. This file is the operator handoff after that repair. The live 8/8 from stamp `20261026T072940388555Z` was scored before the test-gate fix. It is not the post-fix rate. Decisions: [AUTONOMOUS-DECISIONS-2026-10-26.md](AUTONOMOUS-DECISIONS-2026-10-26.md).

## What item 1 built

`./pfy build --local "<task>"` runs a local OpenCode agent in a new git worktree under `<repo>/tmp/`, gates on the test command, and on PASS commits one branch `local/<slug>-<stamp>`. It does not push, does not open a PR, and does not commit in the checkout it was started from.

Cloud `./pfy build` (`scripts/pfy_build_p.py`) is unchanged. `--local` anywhere in argv is the switch. The shell `exec`s the local runner so SIGTERM reaches Python.

## Usage

```text
./pfy build --local "<task>" [--repo DIR] [--base REF] [--model TAG]
    [--endpoint URL] [--test-cmd CMD] [--timeout SEC] [--test-timeout SEC]
    [--min-free-gb N] [--protect GLOB] [--writable-test GLOB]
    [--receipt-dir DIR] [--keep-worktree] [--keep-model] [--unload-at-end]
    [--run-tests-on-timeout] [--dry-run] [--reap] [--unsafe-no-sandbox]
./pfy build --local --prompt-file FILE [same flags]
./pfy build --local --reap [--repo DIR]
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
| `--protect` |  | none, repeatable. A hit is `protected-path-changed` before the test gate |
| `--writable-test` |  | none, repeatable. Those paths are left out of the test-file hash |
| `--reap` |  | off. With no task, exit 0 after stale-group recovery |
| `--unsafe-no-sandbox` |  | off. Used only when bwrap is missing. A working bwrap still runs |
| `--receipt-dir` |  | `<repo>/pipelines/dogfood/build-local/<stamp>/` |

`--keep-model` skips unload unless `--unload-at-end` is also set. A single `./pfy build --local` unloads only a model that this run loaded. `--dry-run` runs the pre-flight checks, prints the plan, starts nothing, and loads nothing.

## Receipt schema `pfy-local-build/1`

File: `<receipt-dir>/receipt.json`, written atomically, including on BLOCKED (then `worktree` is null).

Fields: `schema`, `id`, `task` (first 500 chars, redacted), `repo`, `base_sha`, `model`, `endpoint` (host only), `status` (`PASS|FAIL|BLOCKED|TIMEOUT|ABORTED`), `reason`, `exit_code`, `wall_seconds`, `agent_seconds`, `tests_before`, `tests_after`, `files_changed`, `branch`, `commit`, `worktree`, `model_was_loaded`, `unloaded`, `mem` (`mem_available_gb`, `swap_free_gb`, `min_available_gb`), `opencode_version`, `agent_log`, `sandbox` (`bwrap-unshare-net`, `bwrap-share-net`, or `unsafe-no-sandbox`), `started_at`, `finished_at` (UTC, `Z`).

`password: x` redacts to `password:***`. Token, key, and secret assignments redact the same way.

`tests_before` and `tests_after`: `cmd`, `exit`, `passed`, `failed`, `errors`, `seconds`, `tail` (last 40 lines, redacted).

Summary line: `PASS|FAIL|BLOCKED:|TIMEOUT <reason> branch=<name|none> receipt=<path>`.

Exit codes: 0 PASS, a clean dry-run, or `--reap`. 1 FAIL. 2 usage, or `no-opencode`. 3 TIMEOUT. 4 BLOCKED (`mem`, `busy-host`, a failing `/api/ps`, `model-too-big`, `cloud-tag`, `another run`, `no-model`, `no-sandbox`).

## Guards, fail, recover

| Fail | Exit | Reason | Recover |
|---|---|---|---|
| `MemAvailable + SwapFree` below `--min-free-gb` | 4 | `mem` | free memory. Full swap counts as 0. `SwapTotal` is not free |
| another model loaded | 4 | `busy-host` | that model unloads on its own. This tool does not unload it |
| model size over 30 GiB | 4 | `model-too-big` | pick a smaller tag |
| tag contains `:cloud` | 4 | `cloud-tag` | pick a local tag |
| `opencode` missing | 2 | `no-opencode` | `./pfy attach opencode` |
| Ollama down or tag missing | 4 | `no-model` | start Ollama, or name a tag it lists |
| `/api/ps` is not 200, times out, or is not JSON | 4 | `busy-host` | the guard fails closed. It does not fall through to `ollama ps` |
| bwrap missing and no `--unsafe-no-sandbox` | 4 | `no-sandbox` | install bwrap, or pass the flag and accept `unsafe-no-sandbox` on the receipt |
| lock held by a live pid | 4 | `another run` | wait. A dead pid's lock does not block. `--reap` while the lock is held is the same BLOCKED |
| agent edits nothing | 1 | `no-change` | a real edit |
| a `--protect` path changes | 1 | `protected-path-changed` | leave those paths alone. This fires before the test command |
| tests fail, a new skip, or a new xfail | 1 | `tests-failed` | fix the code. Do not skip the failure |
| fewer tests than before, even if exit 0 | 1 | `tests-regressed` | do not delete tests |
| test file bytes change and the judge did not already fail | 1 | `tests-tampered` | do not rewrite asserts. `--writable-test` is the only exception |
| the same command fails on the second run | 1 | `tests-flaky` | no commit |
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

The runner writes `pipelines/dogfood/build-local-eval/<stamp>/summary.json` and `summary.md` (gitignored). Exit 0 when every scored task passed, or when the run is a named skip. Exit 1 when pass is below passed+failed+blocked, or when the runner broke. Exit 2 when `--require-live` and a skip fired. The old exit-0-on-a-low-rate contract is gone.

`PFY_LOCAL_BUILD_UNSAFE_NO_SANDBOX=1` forwards `--unsafe-no-sandbox`. Without it, a missing bwrap is `BLOCKED` `no-sandbox`. The product does not turn that flag on by itself.

Skips, printed as `SKIP: <reason>`: `opencode-missing`, `ollama-unreachable`, `model-missing <tag>`, `mem-guard <gib>`, `busy-host <model>`, `busy-host unknown` (the ps call failed). A BLOCKED task stops the run. Later tasks are `not-run`. A skip or a BLOCKED task is not a pass.

All eight tasks protect `tests/*`, `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg`, and `tox.ini`. The reference patches only touch `src/`. The offline stub that rewrites asserts to `assertTrue(True)` scores 0.

Tasks stay on one model load: every build uses `--keep-model`, and the last build uses `--unload-at-end` only if this eval loaded the model. A model that was already loaded is left loaded.

## Live result

### Stale, scored before B1

Stamp `20261026T072940388555Z` on host `nimo`, model `qwen3.6:35b`, endpoint `127.0.0.1:11434`. Eval exit 0. Pass rate 8/8 (1.0). Total 571.668 s. Mean 71.459 s. No failures. CONTEXT while loaded was 262144, so there is no `context_warning`. Ollama was not reconfigured. This number is not evidence for the repaired gate. The offline stub cheater, not a live model, is what scores 0 against `assertTrue(True)` on t01, t04, and t08.

### First rerun, aborted

Stamp `20261027T030049105086Z`. Preflight at 2026-10-27T03:00:49Z: MemAvailable about 54.1 GiB, SwapFree about 1.0 GiB, `ollama ps` empty. t01, t02, and t03 returned `FAIL` `no-change` in about 83 s. OpenCode's stderr was `Cannot connect to API: The socket connection was closed unexpectedly.` Ollama never showed the model. Cause: the loopback bridge used a 3 second connect timeout and left that timeout on the proxied socket, so a quiet model load was cut off. A slow-upstream test fails in 4.1 s without `settimeout(None)` after the handshake (`RemoteDisconnected`). The run was stopped at t04 (`interrupted`). It is not a pass rate.

### Post-fix rerun

Stamp `20261027T031008578576Z` on host `nimo`, model `qwen3.6:35b`, endpoint `127.0.0.1:11434`. Eval exit 0. Pass rate 8/8 (1.0). Total 608.235 s. Mean 76.029 s. No failures, no blocked, no not-run. Every task used `bwrap-unshare-net`. Every task had `tests_before.exit` 1 and `tests_after.exit` 0.

A probe in this session had already loaded the model, so each receipt says `model_was_loaded` true and `unloaded` false. The eval did not unload a model it had not loaded. After the receipts were copied, this session ran `ollama stop qwen3.6:35b`. `ollama ps` was then empty. While loaded, `context_length` was 262144, so there is no `context_warning` and Ollama was not reconfigured.

The offline stub that rewrites asserts to `assertTrue(True)` scores 0. That is `test_cheat_asserts_scores_zero_on_t01_t04_t08`, not a live model.

| id | status | reason | wall_s |
|---|---|---|---|
| t01-fix-off-by-one | PASS | ok | 64.433 |
| t02-add-function | PASS | ok | 67.241 |
| t03-rename-symbol | PASS | ok | 77.470 |
| t04-fix-mutable-default | PASS | ok | 117.812 |
| t05-add-cli-flag | PASS | ok | 58.887 |
| t06-parse-duration | PASS | ok | 50.177 |
| t07-remove-dead-code | PASS | ok | 73.012 |
| t08-fix-unicode-strip | PASS | ok | 99.203 |

Committed summary: [live-20261027T031008578576Z.md](../../eval/local-build/live-20261027T031008578576Z.md). Raw receipts stay gitignored under `pipelines/dogfood/build-local-eval/20261027T031008578576Z/`.

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

Can `./pfy build --local` replace Grok Build on a build-only run today? For these eight tiny fixtures, the post-fix rerun passed 8/8 in 608 s on `qwen3.6:35b` inside bubblewrap. A real task from `docs/TODO.md` is still unmeasured (MVP-2). Cloud `./pfy build` is a different program and was not edited.

## Sandbox

The agent runs under bubblewrap when `bwrap` works. The root is read-only. The worktree is read-write. The main checkout, `~/.ssh`, `~/.config/gh`, `~/.grok`, the git common dir, and the git dir are hidden. A hidden directory that is an ancestor of the worktree is a tmpfs, then `--dir` rebuilds the path, then the worktree is bound.

Loopback Ollama uses `--unshare-net` plus one AF_UNIX to TCP splice. The TCP connect allows 3 seconds for the handshake, then the proxied socket blocks for the whole response. Leaving that timeout on the socket cut off a quiet model load and OpenCode reported a closed socket. The socket inode is under the worktree `tmp/`. The name is a short symlink in `XDG_RUNTIME_DIR` or `/run/user/$UID`, because `sun_path` is 108 bytes and this worktree path is longer. That is not `/tmp`. `/run` stays read-only inside the sandbox, so the agent cannot replace the symlink. The listener is a daemon thread in a wrapper that `subprocess.call`s the agent. A forked listener kept bwrap alive after the HTTP response and was reparented to the user systemd.

A non-loopback endpoint uses `--share-net`. Git lockdown still applies. Missing bwrap without `--unsafe-no-sandbox` is `BLOCKED` `no-sandbox`. The flag does not disable a working bwrap.

For a linked worktree, `.git` points at `worktree/tmp/git-sandbox` during the agent only. That dir is seeded with the worktree files and has no remotes. `pushurl` is `file:///pfy-local-build-push-blocked`, hooks are an empty directory, and the credential helper is empty. The caller's common git config is not edited. The original `.git` bytes are restored before the product commit. `GIT_CONFIG_*` is on the agent environment only. If `.git` is not a file, the swap is skipped and the read-only filesystem is the boundary.

Opencode's permission file stays, as defence in depth. It is not the boundary. The home for that file is `worktree/tmp/opencode.home` and is deleted after the run, along with the lock and the pid file.

## Known gaps

- Confinement is bwrap 0.11.1 as the same uid. It is not a separate user. It is not a claim about a kernel bug or a bwrap bug.
- Egress is closed only in `bwrap-unshare-net`, and even then one port reaches the local Ollama. `bwrap-share-net` shares the network namespace. Curl to the wider network is possible in that mode. Push is still blocked by the sandbox git dir and the read-only root, which the black-box tests demonstrated for the five push forms and for `python` `open()` of a host file.
- SIGKILL of the runner cannot write its own receipt. The next run and `pfy build --local --reap` kill a dead pid's recorded group, write `ABORTED` for a `build-local` directory with no receipt, and unload the model only if `loaded_by_run` is set. A live recorded pid is left alone, because the pid may have been recycled. If the process dies before the pid file exists, there is nothing to reap.
- The agent group gets SIGTERM, five seconds, then SIGKILL, including after the leader has exited. A child that ignores SIGTERM still dies on SIGKILL. That grace is why a hang is not instant.
- Ubuntu CI history: `CloudBuildUnchangedTests` used to need `grok` and a full help golden that differs across Python versions. It now skips when `grok` is missing, checks stable substrings and exit codes, and deletes any new file under `pipelines/dogfood/build/`. Behavior tests add `--unsafe-no-sandbox` only when that process cannot run bwrap, so a runner without bwrap is not a new red. `SandboxEscapeTests` skip only in that case. This box ran them. Nothing was apt-installed.
- Python 3.13 is not on this box and was not installed. Python 3.14.4: 901 tests, 623.379 s, 1 failure, 16 skipped. The failure is `test_relative_outdir_log_path_safe` because `TMPDIR` is inside the repo. Python 3.12.12 (uv prefix): 901 tests, 552.107 s, 21 failures, 16 skipped. One is that same outdir case. The other 20 are `tests.test_harness2_local_sandbox`: the sandbox tries to exec `sys.executable`, and the uv binary lives under the home that sandbox hides (`FileNotFoundError` on that path). The same tree passed those tests under `/usr/bin/python3`. They are not in the fix-1 diff. The hedge detector and the two lab-stage cases did not fail on either run (Ollama was up).
- One model at a time. A second loaded model is `BLOCKED: busy-host`, and this tool does not unload it. A failed `/api/ps` is the same BLOCKED, not an `ollama ps` fallback.
- The default test command is `python3 -m unittest discover -s tests -t .`. Other stacks need `--test-cmd`.
- If a host's Ollama context is below 16384, the runner records `context_warning` and does not reconfigure Ollama. The stale run's context was 262144.
- No push and no PR, by design. The branch stays in the repo's `tmp/` worktree. On PASS that worktree is removed.
- The fixtures are eight tiny tasks. They are not a cost or pass-rate comparison against cloud `./pfy build`.
- Daemon splice threads can emit `ResourceWarning` for sockets they do not close. The bridge test still passes.

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
- RED: remove the test-file hash -> test_rewriting_asserts_to_true_does_not_commit (PASS, exit 0, assertion 0 != 1)
- RED: remove the kill on leader exit and the post-loop kill -> test_orphan_background_does_not_block (TimeoutExpired at 25 s)
- RED: run_sandboxed returns the raw argv -> test_push_forms_and_secret_write_do_not_leak (bare SHA changed)

## Status

- Branch: `bot/mvp-local-build`
- Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/mvp-local-build
- Base: `7b716e86d5a3df3281b262ac15ec0b254f448041`
- item 1: DONE. `b63d8d011ebe95558c35101c2f62d1a23975f861`. 25 behavior tests.
- item 2: DONE. `fbbaf90bc5a245d5ca69f274b610c68f369f3664`. 13 behavior tests.
- item 3: DONE at the time, `da2ce97`. Live 8/8, 571.668 s. That 8/8 is stale after the gate FAIL.
- item 4: the first handoff, `e63a95b`. Tester and Reviewer then failed that SHA.
- fix 1: merge of `origin/main` is `008c7b2` (`2f2b20e`, catalog only). Post-fix live stamp `20261027T031008578576Z`, 8/8, 608.235 s, context 262144. The head after the docs commit is `git rev-parse HEAD` on this branch. A commit cannot record its own SHA.
- fix 1 suites: Python 3.14.4, 901 tests, 623.379 s, failures=1, skipped=16. Python 3.12.12, 901 tests, 552.107 s, failures=21, skipped=16. Python 3.13 absent. Details are under Known gaps. Hedge detector and lab_stage did not fail.
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
