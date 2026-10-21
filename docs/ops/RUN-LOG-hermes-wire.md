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
