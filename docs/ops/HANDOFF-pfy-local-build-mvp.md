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

## Status

- item 1: DONE in this worktree, behavior tests green (25). RED lines are in `docs/ops/RUN-LOG-pfy-local-build-mvp.md`.
- item 2: not started
- item 3: not started. Live model load only after items 1 and 2 are committed, and only behind the quiet-host gates.
- item 4: this handoff is the running copy. Final SHA, test counts, local CI, and the replace-Grok-Build line land at the end.
- Exit: none yet. STOP file absent.
