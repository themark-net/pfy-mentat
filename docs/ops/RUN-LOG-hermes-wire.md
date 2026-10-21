Tue Oct 20 11:41:46 PM PDT 2026

# RUN-LOG hermes-wire

START: 2026-10-20 23:41:46 PT (`date` above).
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire`
Branch: `bot/hermes-wire`
HEAD at start: `e9365d545e52dcb7a319377c87edf32e1c7dce0a` (equals `origin/main` and `origin/bot/hermes-wire` after `git fetch`).
STOP file: absent.
Clock: no new item after 2026-10-21 05:41 PT. Stop work by 2026-10-21 07:11 PT. Hard kill 2026-10-21 07:41 PT. Live 27-task re-run only if started by 2026-10-21 04:26 PT.
`~/.hermes` snapshot before: 113616 paths (path, mtime, size) in `tmp/hermes-snapshot-before.json`. Contents not read.
Ollama at start: tags include `qwen3.6:35b`, `ollama ps` empty. bwrap present. System `~/.local/bin/hermes` not used.

## Decisions

- 2026-10-20 23:45 PT: TTFT stamps are UTC ISO-8601 with milliseconds and a Zulu suffix. `parse_ts` rejects a whole-second stamp. Decision: fail closed rather than truncate.
- 2026-10-20 23:45 PT: Hermes wording follows the code. Each task is a new `subprocess` of `hermes_arm.py`. `AIAgent.run_conversation` is the library call inside that process.
- 2026-10-20 23:54 PT: The unittest suite runs with TMPDIR unset. `test_relative_outdir_log_path_safe` treats a temp dir inside the repo as in-tree, so pointing TMPDIR at `$W/tmp` fails that test. Scratch for this run stays under `$W/tmp`. CI-shaped suite uses the default temp dir.

## Item 0

- 2026-10-20 23:45 PT: start R1 R2 R3. STOP absent.
- R1: rewrote the in-process sentence in `docs/eval/HERMES-EVAL-HANDOFF.md`. `git grep -n in-process -- docs/eval examples/hermes-bakeoff pipelines/dogfood/hermes-bakeoff` is empty after the edit.
- R2: summary line in `docs/eval/hermes-vs-current.md` links "much faster" to the not-like-for-like note (thinking off on Hermes only, opencode CLI cold start, RSS excludes the model).
- R3: MCP log stamp and `ttft_s` use millisecond stamps. RED: `stamp_now` forced to `%Y-%m-%dT%H:%M:%SZ` -> `test_ttft_keeps_milliseconds_and_rejects_whole_second_stamps` FAILED (regex). Restored. Same test then OK.
- 2026-10-20 23:59 PT: `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 618 tests in 375.711s, OK (skipped=14), EXIT 0. An earlier run with `TMPDIR=$W/tmp/tmpdir` failed `test_relative_outdir_log_path_safe` (in-repo temp counted as in-tree) and raced `test_module_run_leaves_no_new_tmp_dirs` against other `/tmp/pfy-*` dirs. Those two tests pass with TMPDIR unset.

## Item 1

- 2026-10-21 00:08 PT: start prerequisites. STOP absent. `date` Wed Oct 21 12:08:31 AM PDT 2026. Ollama `ps` empty. MemAvailable about 51.7 GiB.
- Decision: review commit `24fe672` says 14 of 20 scorer mutants survive and does not name them. This run uses the 20 named below. The e215cb8 tests kill 5. The `!=` to `==` mutant survives those tests (the wrong-args case still mismatches on a later key) and is killed by a new accept assertion on the same test. The other 14 survive the e215cb8 file and die on the new tests. Each mutant was restored. Nothing mutant was committed.
- RED 1 narrate always `return False` -> `test_narrate_detects_fenced_json_and_ignores_a_real_call` FAIL. Old file also killed it.
- RED 2 narrate guard forced `False and` -> same narrate test FAIL (server-seen call still flagged). Old file also killed it.
- RED 3 `_args_match` `!=` flipped to `==` -> wrong-args rejection alone stayed green. Accept path `assertTrue` on the matching call FAIL. Old e215cb8 file stayed green. Restored test OK after deleting a same-second `score` pyc (equal-length mutant, timestamp resolution is one second).
- RED 4 margin `+ 0.10` to `+ 0.0` -> `test_margin_just_below_ten_points_is_no_win` FAIL (0.599 scored WIN). Old file killed it.
- RED 5 peak gate `2 * GIB` to `200 * GIB` -> same margin test FAIL. Old file killed it.
- RED 6 `tool_call` unwrap dropped -> `test_hermes_tool_call_wrapper_is_not_a_second_invalid_attempt` FAIL. Old file killed it.
- RED 7 percentile rank `len * pct` -> `test_percentile_wilson_and_aggregate_lock_the_rates` FAIL (p50 30 != 25). Old file stayed green.
- RED 8 empty percentile returns `0.0` -> same rates test FAIL (`0.0` is not `None`). Old file stayed green.
- RED 9 no interpolation (`return ordered[low]`) -> same rates test FAIL (20 != 25). Old file stayed green.
- RED 10 `wilson(0, 0)` returns `(1, 1)` -> same rates test FAIL. Old file stayed green.
- RED 11 wilson returns `(p, p)` -> same rates test FAIL (width not > 0.1). Old file stayed green.
- RED 12 wilson bounds swapped -> same rates test FAIL (`low < p` fails). Old file stayed green.
- RED 13 task success `(k + 1) / n` -> same rates test FAIL (1.0 != 0.5). Old file stayed green.
- RED 14 empty-attempt valid rate `0.0` -> same rates test FAIL (quiet row 0.0 != 1.0). Old file stayed green.
- RED 15 narrate rate over `n` not `len(required)` -> same rates test FAIL (0.5 != 1.0). Old file stayed green.
- RED 16 peak is `min` -> same rates test FAIL (100 != 500). Old file stayed green.
- RED 17 unmatched client not counted -> `test_negative_wrong_text_fails_and_unmatched_client_is_an_attempt` FAIL (`(0, 0)` != `(1, 0)`). Old file stayed green.
- RED 18 `_valid_calls` ignores `schema_valid` -> `test_schema_invalid_right_args_do_not_pass` FAIL. Old file stayed green (its invalid call also has wrong args).
- RED 19 `submits[-1]` to `submits[0]` -> `test_last_submit_wins_and_a_contained_string_does_not` FAIL. Old file stayed green.
- RED 20 negative ignores text -> `test_negative_wrong_text_fails_and_unmatched_client_is_an_attempt` FAIL (`"nope"` passed). Old file stayed green.
- RED s2 drift check forced off -> `test_fetch_oracle_follows_the_fixture_not_a_stale_label` FAIL (stale label passed).
- RED s3 `labels_written` hardcoded `2026-10-19T18:00:00Z` -> `test_labels_written_is_the_newest_source_stamp` FAIL. Live stamp is `2026-10-06T16:01:36Z` (max of laya, local-bench-3, local-bench-5, atg-compile).
- RED s4 `meta.started` stamped after the closing `/api/ps` -> `test_run_records_start_before_the_closing_ollama_ps` FAIL.
- RED s6 rescore reads `./tmp/bakeoff/full1` -> `test_rescore_reads_the_committed_receipt_only` FAIL (`IsADirectoryError` from the temp cwd).
- RED s7 `bakeoff_` strip removed -> `test_mcp_server_accepts_both_wire_prefixes` FAIL (`bakeoff_submit_choice` no longer becomes `submit_choice`).
- 2026-10-21 00:15 PT: campaign restore checked (`git diff --stat` is only the Item 1 files). STOP absent. `date` Wed Oct 21 12:15:45 AM PDT 2026.
- 2026-10-21 00:22 PT: `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 628 tests in 376.975s, OK (skipped=14), EXIT 0. Em dash check on `git diff origin/main` was empty.
- 2026-10-21 00:24 PT: Item 1 pushed `9f44be1` to `origin/bot/hermes-wire`.

## Item 2

- 2026-10-21 00:24 PT: start re-run harness. STOP absent. `date` Wed Oct 21 12:24:14 AM PDT 2026. Latest live start is still 2026-10-21 04:26 PT.
- Decision: thinking stays off on both arms. A stdlib proxy forces `think=false`, `temperature=0`, `seed=1`, `reasoning_effort=none` on `/v1/chat/completions` and `/api/chat`. Unload `POST /api/generate` is not rewritten. The proxy log does not store prompts.
- Decision: Hermes config sets `tools.tool_search.enabled: off` so the tool_search bridge stays off and MCP tools are offered directly. Checkout copied to `$W/tmp/hermes-agent` at `ddabd383`. Venv copied to `$W/tmp/.venv-hermes`. Its python symlink still points at the eval worktree uv runtime and this run does not write that tree.
- Decision: bake-off child `TMPDIR` is `<repo>/tmp/tmpdir`, or `TMPDIR` when that path is already under `<repo>/tmp`. It is not `/tmp`.
- RED: delete the `tools.tool_search` block -> `test_hermes_config_turns_tool_search_off` FAIL. Restored.
- RED: chat body drops `think` instead of forcing false -> `test_think_proxy_forces_chat_and_leaves_unload_alone` ERROR (missing think). Restored.
- 2026-10-21 00:26 PT: `tests.test_hermes_bakeoff` Ran 23 tests in 3.219s, OK, before the full suite. `date` Wed Oct 21 12:26:18 AM PDT 2026.
- Decision: bake-off children get `PYTHONDONTWRITEBYTECODE=1` so imports do not write bytecode into the copied checkout or the uv runtime the venv symlink still points at.
- 2026-10-21 00:33 PT: `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 631 tests in 379.367s, OK (skipped=14), EXIT 0. That run was before the bytecode env line. Re-running the suite with the line in place before the push. `date` Wed Oct 21 12:33:02 AM PDT 2026. STOP absent. Ollama `ps` empty. MemAvailable 51870352 kB.
- 2026-10-21 00:40 PT: suite again with `PYTHONDONTWRITEBYTECODE=1` in the child env -> Ran 631 tests in 379.086s, OK (skipped=14), EXIT 0. Em dash check empty. `date` Wed Oct 21 12:40:08 AM PDT 2026. STOP absent. Ollama `ps` empty. MemAvailable 52838128 kB.
- 2026-10-21 00:40 PT: live re-run starts after this push. Command: `bash tmp/run-rerun.sh` (27 tasks, num_ctx 65536, out `pipelines/dogfood/hermes-bakeoff/results-rerun.json`, does not overwrite `results.json`).
- 2026-10-21 00:43 PT: live run in progress. STOP absent. `date` Wed Oct 21 12:43:54 AM PDT 2026. Decision: do not run the full suite and do not unload `qwen3.6:35b` while the bake-off holds the model. The `baseline` directory is the opencode arm.
- 2026-10-21 00:47 PT: live run finished. `date` Wed Oct 21 12:47:40 AM PDT 2026. STOP absent. `RUN_EXIT 0`. `ollama ps` empty. Verdict NO-WIN. Hermes 26/27 vs opencode 26/27. Valid 36/36 vs 36/36. p50 7.011s vs 7.191s. TTFT p50 4.877s vs 5.364s (no whole-second values). Peak 239.8 MiB vs 1.03 GiB. Meta calls 0. Proxy forced 153 chat completions. Requested num_ctx 65536, observed context_length 262144. Both arms miss only `ch-ph-08-missing-ci` with one `hold` (label `escalate`).
- Decision: the import smoke at 00:17 PT used the eval venv python with `HERMES_HOME` unset, and Hermes seeded `~/.hermes` (legacy SOUL.md replaced, backup and cache files added). Restored the 537-byte legacy scaffold and removed the eight added paths. Snapshot diff after the restore is empty (113616 paths). Contents were not printed.
- 2026-10-21 00:47 PT: Item 3 code is in the tree. Decision: `PFY_BOT_INTERFACE` default stays opencode. Hermes runs only when the flag is `hermes`, the checkout and python exist, and the home is not `~/.hermes`. Missing checkout falls back to opencode and does not run the installer. Model server down starts neither agent.

## Item 3

- 2026-10-21 00:43 PT: plan `docs/plans/hermes-bot-interface.md` is in the tree before the flag. `date` during this item Wed Oct 21 12:43:54 AM PDT 2026, continued after the re-run. STOP absent.
- Decision: `./pfy bot` execs `pfylib/bot_interface.py`. `./pfy attach hermes` is unchanged.
- 2026-10-21 00:47 PT: `env -u TMPDIR python3 -m unittest tests.test_bot_interface` -> Ran 9 tests in 3.850s, OK. Covers default opencode, missing Hermes falling back, both binaries missing, model server down (no child), malformed tool call, timeout kill, real `~/.hermes` refused, driver missing checkout. Full suite waits until the model is unloaded, then runs before the push.
- 2026-10-21 01:02 PT: `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 640 tests in 409.171s, OK (skipped=14), EXIT 0. `date` Wed Oct 21 01:02:12 AM PDT 2026. STOP absent. `ollama ps` empty. Em dash check: no added line contains U+2014. The diff hunk header still quotes the pre-existing `pfy` usage line.
- 2026-10-21 01:02 PT: bot flag pushed `56961bb`. Re-run receipt and write-up pushed `3500119`.
- 2026-10-21 01:03 PT: `~/.hermes` snapshot diff empty again (113616 paths, added 0, removed 0, changed 0). `openclaw-gateway` inactive and disabled. STOP absent. `date` Wed Oct 21 01:03:34 AM PDT 2026.
- 2026-10-21 01:04 PT: handoff commit `43391e1f0913932a67bdfd161e0ceea47edbc8a3`. Stamp commit `dee785691e1351b5f4a393e45d462d350844879a`.
- 2026-10-21 01:10 PT: second suite `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 640 tests in 388.186s, OK (skipped=14), EXIT 0. Pushed `43391e1` `dee7856` `363eefb`. `ollama ps` empty. STOP absent. `date` Wed Oct 21 01:10:43 AM PDT 2026.
- 2026-10-21 08:05 PT: post-session check. Grok log ended with an end event (end_turn, 212 turns). PIDs 2858753 and 2858754 gone. origin/main still `e9365d5`, no merge needed. No added line vs main contains U+2014. `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 640 tests in 396.995s, OK (skipped=14). `ollama ps` empty. Handoff status set to ready to gate.
- 2026-10-21 08:35 PT: CI round 1 (run 39622614753 on `aa42b63`) red on ubuntu: `test_run_records_start_before_the_closing_ollama_ps` timed out at 60s because `wait_for_memory` waits for the 47 GiB real-model floor and the runner has far less. Fix: `HERMES_BAKEOFF_MEM_FLOOR_KIB` env override in `wait_for_memory`, set to 0 by that test, plus `test_memory_gate_override_returns_without_waiting`. RED: without the override the new test hung and `timeout 20` exited 124. Restored. `tests.test_hermes_bakeoff` Ran 24 tests OK. Full suite `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 641 tests in 382.185s, OK (skipped=14). The nimo job's catalog step also failed in round 1 while a local structural run overlapped it on the same host (the `/tmp/pfy-*` race in `test_module_run_leaves_no_new_tmp_dirs` noted at 23:59 PT).

## Item 4: Reviewer FAIL fix (B1, B2, nits)

- 2026-10-21 11:27 PT: start. STOP absent. Tip `cbcd65dd92116ec7692e153600a37e5d2086da74`. `origin/main` already in the branch, no merge needed. opencode 1.18.32 at `~/.local/bin/opencode`. `ollama ps` empty. MemAvailable 71624512 kB.
- B1 control: the `cbcd65d` `bot_interface.py` against an in-process stub OpenAI-compatible server (`--model ollama/stub-model`) -> `FAIL: opencode exited 1`, rc 1. Stub log: one `GET /api/tags` (the probe), zero `POST`. opencode never reached the server.
- B1 fix: `run_opencode` writes `tmp/bot-interface/opencode/config/opencode/opencode.json` with an `ollama` provider (`npm` `@ai-sdk/openai-compatible`, `options.baseURL` = `LOCAL_OPENAI_BASE_URL`, `models` lists `PFY_BOT_MODEL`) and sets `OPENCODE_CONFIG` to it. Same stub run after the fix: rc 0, stdout `stub-ok`, stub log `GET /api/tags` then two `POST /v1/chat/completions model=stub-model stream=True`.
- B2 fix: `_run_child` passes `stdin=subprocess.DEVNULL` (both the opencode and Hermes children).
- Isolation: the opencode child gets `HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME` and its cwd under `tmp/bot-interface/opencode/`, plus `OPENCODE_DISABLE_PROJECT_CONFIG=1`, `--pure`, and autoupdate, models fetch, share, Claude Code, external skills, and LSP download turned off. `OPENCODE_CONFIG_CONTENT` from the caller is not passed through (`_scrub` allow-list). `~/.config/opencode` and `~/.opencode` had no file newer than the pre-run snapshot after the real runs below.
- New tests in `tests/test_bot_interface.py`:
  - `test_open_stdin_pipe_does_not_hang_the_child`: fake opencode reads stdin to EOF while the caller holds a never-closed pipe. RED: drop `stdin=subprocess.DEVNULL` -> FAIL (the child ran into the 8s timeout). Restored.
  - `test_opencode_child_gets_a_provider_for_the_server_and_no_user_config`: fake opencode dumps cwd, env, argv. Asserts the config file names the server `baseURL` and model, `--model ollama/<model>`, every state dir and the cwd under the work dir, and no caller `OPENCODE_CONFIG_CONTENT`. RED: drop `OPENCODE_DISABLE_PROJECT_CONFIG` -> ERROR. Restored.
  - `test_real_opencode_resolves_the_provider_and_reaches_the_server`: real opencode binary against an in-process stub on an ephemeral port, once default and once `PFY_BOT_INTERFACE=hermes` with no checkout (fallback). Asserts rc 0, no `Provider not found`, at least one `POST /v1/chat/completions` with the configured model, and the stub reply on stdout. Skips with reason `opencode binary not found on PATH or PFY_BOT_OPENCODE` when the binary is absent (ubuntu CI). RED: rename the `provider` key -> both subtests FAIL (rc 1). Restored.
- `tests.test_bot_interface`: Ran 12 tests in 8.4s, OK on nimo (E2E ran, not skipped).
- Code commit `fb5e34d4a6f850fd04ddb01c7053f115d204ce05`.

### Real `./pfy bot` runs on nimo ollama at `fb5e34d`

Script `tmp/b1/real-runs.sh` (gitignored), output `tmp/b1/real-runs.log`. `PFY_BOT_MODEL=qwen3.6:35b PFY_BOT_TIMEOUT=600`, stdin `/dev/null`, prompt `Reply with exactly one word: pong`. Evidence is the Ollama service journal (`journalctl -u ollama`), the window starts at each run's start second so the first line can be the previous run's last request.

| Run | Command | rc | Time | Stdout | Ollama requests in window |
|---|---|---:|---:|---|---|
| default (11:32:18 PT) | `./pfy bot "Reply with exactly one word: pong"` | 0 | 58.0s (cold load) | `bot interface: opencode`, `pong` | `GET /api/tags`, `POST /v1/chat/completions` 200 (45.5s), `POST /v1/chat/completions` 200 (56.2s) |
| hermes (11:33:16 PT) | `PFY_BOT_INTERFACE=hermes ./pfy bot "..."` (worktree checkout `tmp/hermes-agent` and `tmp/.venv-hermes` present) | 0 | 33.5s | `bot interface: hermes`, `pong` | `GET /api/tags` x2, `POST /api/show` x7, `POST /v1/chat/completions` 200 (30.0s) |
| hermes fallback (11:33:49 PT) | `PFY_BOT_INTERFACE=hermes PFY_HERMES_CHECKOUT=tmp/b1/no-hermes-checkout ./pfy bot "..."` | 0 | 5.7s | `Hermes checkout or python is missing`, `falling back to opencode`, `bot interface: opencode`, `pong` | `GET /api/tags`, `POST /v1/chat/completions` 200 (3.8s), `POST /v1/chat/completions` 200 (4.2s) |

`ollama ps` was empty before the first run, held `qwen3.6:35b` between runs, and was empty again after `keep_alive: 0`.

### `~/.hermes` sha256 compare

- Before the real runs: sha256 manifest of every path under `~/.hermes` (113616 paths, same count as the 23:42 PT snapshot) in `tmp/b1/hermes-sha-before.json`. After: `tmp/b1/hermes-sha-after.json`. Added 0, removed 0, changed 0. Contents not printed.
- Restored `~/.hermes/SOUL.md` (537 bytes, mtime 2026-06-15 22:18 PT) sha256 `3a10ce135b52753beda81368712decc49a83715d527e00660c19f69d1b4879da`. The `SOUL_EOF` heredoc that `~/.hermes/hermes-agent/scripts/install.sh` (`c6b0eb4`, lines 1733-1747) writes as the legacy scaffold hashes to the same value. The 00:17 PT restore is now a hash match, not only a size match.

### Suite

- 2026-10-21 11:41 PT: `TMPDIR=$W/tmp/tmpdir python3 -m unittest discover -s tests -t .` -> Ran 644 tests in 397.141s, FAILED (failures=1, skipped=14). The one failure is the known `test_relative_outdir_log_path_safe` (temp dir inside the worktree counts as in-tree, see 23:54 PT decision).
- Decision: suite TMPDIR is `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire-suite-tmp`, under the project tmp but outside this worktree, so it is neither `/tmp` nor in-tree. `tests.test_local_bench` with it: Ran 16 tests, OK.
- 2026-10-21 11:48 PT: `TMPDIR=/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire-suite-tmp python3 -m unittest discover -s tests -t .` -> Ran 644 tests in 395.348s, OK (skipped=14), EXIT 0. `origin/main` still in the branch. `ollama ps` empty.
