# Hermes eval check (lane mvp-hermes-check-1031)

Checked 2026-11-01 from this worktree on `bot/mvp-hermes-check-1031`. No local model. No `run.py --live`.

Raw aggregate: `pipelines/dogfood/hermes-bakeoff/results.json` (66,714 bytes). Per-task transcripts under `./tmp/bakeoff/full1/` are not in git and are not in this worktree. Claims that need those transcripts, a live `ollama ps`, or a home-directory snapshot are **unverified**.

Scorer re-run: `score.aggregate` and `score.margin_verdict` on `rows.hermes` and `rows.baseline`. The recomputed summary matches the stored `summary` field for every key, including Wilson bounds. The recomputed verdict is `NO-WIN` with the same two reason strings. `wilson_overlap` recomputes to true.

Display rounding below is Python 3 `round` (half even) to the precision printed in the docs. Rates are `k/n`, not the stored float printed first.

Offline check: `nice -n 19 python3 -m unittest tests.test_hermes_bakeoff -v` on 2026-11-01T01:39Z. `Ran 9 tests in 0.658s` `OK`. No model call. `pytest` is not installed here, so the handoff's pytest line was not re-executed.

## Corrections in this check

Two claims did not match the tree. Docs only.

1. "Labels fixed before the scored calls" / "labels before the run". `labels_before_models` is true, but `labels_written` is the hardcoded `2026-10-19T18:00:00Z`, which is later than `meta.started` `2026-10-19T08:33:09Z`. The tasks file first appears in `b48d634`, the same commit as the results. Corrected in `docs/eval/hermes-vs-current.md`, `docs/eval/HERMES-EVAL-HANDOFF.md`, and `examples/hermes-bakeoff/README.md`.
2. "+10 points means about three more baseline misses." The current gap is 1/27 = 3.70 pp. Two more baseline misses, Hermes still 26/27, is (26-23)/27 = 11.11 pp, which clears +10 pp. One more miss is 7.41 pp, which does not. Corrected in `docs/eval/hermes-vs-current.md`.

How this fails: a reader treats the stamp or the "about three" sentence as the measured gap. How it recovers: the sentences now show the two clocks and the one-miss / two-miss arithmetic. No code change, so no new test. The offline unittest still passes and does not call a model.

## Headline metrics

Source rows are `results.json` `rows`, recomputed with `score.aggregate`. Stored `summary` matches.

| Claim | Source | Recomputed | Match |
|---|---|---|---|
| Verdict NO-WIN | `docs/eval/hermes-vs-current.md`, `docs/eval/HERMES-EVAL-HANDOFF.md`, `results.json` `verdict` | `margin_verdict` returns NO-WIN | yes |
| Task success Hermes 26/27 = 96.30% | both eval docs, `sources/entries/134-hermes-agent.md`, `docs/PENDING-HANDOFF.md` | 26 pass / 27 = 96.296...% rounds to 96.30% | yes |
| Task success opencode 25/27 = 92.59% | same four files | 25/27 = 92.592...% rounds to 92.59% | yes |
| Gap +3.70 pp, short of +10 pp | same four files | (1/27)*100 = 3.7037 pp rounds to 3.70. Bar in `score.margin_verdict` is +10 pp | yes |
| Wilson Hermes 81.7% to 99.3% | both eval docs | `wilson(26, 27)` = 0.81716 to 0.99343, rounds to 81.7% and 99.3% | yes |
| Wilson opencode 76.6% to 97.9% | both eval docs | `wilson(25, 27)` = 0.76630 to 0.97945, rounds to 76.6% and 97.9% | yes |
| Wilson intervals overlap | both eval docs, `results.json` `wilson_overlap` | `intervals_overlap` is true | yes |
| Valid tool-call rate Hermes 38/46 = 82.61% | both eval docs and the two repeats | 38/46 = 82.6087% rounds to 82.61% | yes |
| Valid tool-call rate opencode 45/46 = 97.83% | same | 45/46 = 97.8261% rounds to 97.83% | yes |
| Valid rate minus 15.2 pp, worse than 2 pp | both eval docs, entry 134, pending handoff | (38/46 - 45/46)*100 = -15.217 pp rounds to -15.2. Rule fails when Hermes is more than 2 pp under | yes |
| Narrate rate 0/24 = 0 on both arms | `hermes-vs-current.md` metrics table | `narrate_n` 0, `narrate_tasks` 24 (rows with `requires_call`), both arms | yes |
| Latency Hermes p50 / p95 / mean 8.75s / 13.65s / 9.63s | metrics table | 8.749 / 13.6465 / 9.63281, round to 8.75 / 13.65 / 9.63 | yes |
| Latency opencode p50 / p95 / mean 47.38s / 60.98s / 46.27s | metrics table and the p50 repeats (8.75 vs 47.38) | 47.377 / 60.981 / 46.2747, round to 47.38 / 60.98 / 46.27 | yes |
| p50 ratio 0.18x, pass (not over 1.5x) | metrics table | 8.749/47.377 = 0.1847 rounds to 0.18. 0.18x is under 1.5x | yes |
| Time to first tool call p50 6.44s vs 42.00s | metrics table | 6.438 rounds to 6.44. 42.004 rounds to 42.00. None ttft rows are dropped by `aggregate` (3 Hermes, 4 opencode) | yes |
| Agent peak RSS 221 MiB vs 1.04 GiB, Hermes under 2 GiB | both eval docs, entry 134, pending handoff | max `peak_rss_bytes` 232243200 = 221.484 MiB rounds to 221. 1112133632 = 1.0358 GiB rounds to 1.04. 221 MiB is under 2 GiB | yes |
| Hermes meta calls 52, opencode 0, not in the valid rate | metrics table and method section | sum of row `meta_calls` is 52 and 0. `aggregate` does not add them to `attempts` | yes |
| Model `qwen3.6:35b`, Ollama 0.30.8, Hermes pin `ddabd3837862022a6053331fe3ba97cf9716b9e3`, driver `AIAgent.run_conversation`, opencode 1.18.32 | both eval docs `meta` | same strings in `results.json` `meta` | yes |
| Timeout 180s, max rounds 6, Hermes temperature 0, seed 1, `think` false | method section and `meta` | `timeout_s` 180, `max_iterations` 6, `temperature` 0, `seed` 1, `think` false | yes |
| Requested `num_ctx` 65536, observed `context_length` 262144 | both eval docs | `meta.num_ctx` 65536. `ollama_ps_after_tasks[0].context_length` 262144 | yes |
| One scored pass recorded in this file | `meta.valid_rate_note` "No second model pass" | one `results.json`. The note is in the file. No second aggregate is in the tree | yes for this file. A run that was never committed would be invisible |

## Task set and autopsy

| Claim | Source | Recomputed | Match |
|---|---|---|---|
| 27 tasks | both eval docs, tasks file `n_tasks` | 27 tasks in the JSON, 27 rows each arm | yes |
| 14 choice, 8 fetch, 2 chain, 3 negative | `hermes-vs-current.md` | kind counts 14, 8, 2, 3. Choice ids match the listed ph/wz/hd/fm/cp set | yes |
| Fewer than five tasks failed on each arm | autopsy intro | Hermes fails: `ch-ph-08-missing-ci` only (1). Opencode fails: that case and `ch-wz-06-cloud-grok` (2) | yes |
| Hermes `ch-ph-08-missing-ci` called `submit_choice` `push`, label `escalate`, wall 8.0s | autopsy item 1 | `pass` false, reason names `choice` `escalate`, server call `choice` `push`, `schema_valid` true, `wall_s` 7.998 rounds to 8.0 | yes |
| Excerpt "Local CI green (not known-red) and Kronos idle" | autopsy item 1 | that substring is in `final_text` and in the call `reason` | yes |
| Eight tasks account for 8 invalid Hermes attempts (46 attempts, 38 valid) | autopsy item 2 | 8 Hermes rows with `attempts > valid`, and the extras sum to 8. Totals 46 and 38. The 8 ids are the six `fetch-*` rows `fetch-entry-130-slug`, `fetch-entry-101-slug`, `fetch-grok-stage`, `fetch-bench3-n-correct`, `fetch-bench5-accuracy`, `fetch-bench3-eval-tok-s` (each +1) and both chains `chain-bench-plus-ten`, `chain-kanbots-plus` (each +1) | yes |
| Those 8 invalid calls were empty `submit_answer` and sometimes `compute_sum` with `a: 0`, inside `tool_call`, and never reached the server | autopsy item 2 | not in `results.json`. Server logs for those rows do not store the unmatched client arguments. Transcripts are not committed | unverified |
| 52 meta envelopes; counting them as invalid gives a first-pass rate of 42.2% and of 42% | method section (42.2% and 42%) and autopsy item 3 (42%) | Server calls on Hermes sum to 38, all valid. 38/(38+52) = 42.222...% rounds to 42.2% and to 42%. Adding 52 on top of the published 46 attempts is 38/98 = 38.78%, which the docs do not claim | yes, under the 38+52 reading |
| Opencode `ch-ph-08-missing-ci`: first `push` ("known_red is false"), then `hold` ("CI is unknown"), wall 62.3s | autopsy item 4 | server call order is `push` then `hold`. Reasons contain those substrings. `wall_s` 62.267 rounds to 62.3. Both calls `schema_valid` true, task `pass` false | yes |
| Captured text says `submit_choice` was called once with choice `push` | autopsy item 4 | `final_text` contains that statement. The server log has two calls. The doc reports the captured text, not a claim that only one call landed | yes |
| Hermes passed `ch-wz-06-cloud-grok` with `choice` `grok` in 8.4s | autopsy item 5 | `pass` true, `choice` `grok`, `wall_s` 8.377 rounds to 8.4 | yes |
| Opencode `ch-wz-06-cloud-grok` exit 0 in 49.8s, no MCP call, empty captured text | autopsy item 5 | `returncode` 0, `wall_s` 49.797 rounds to 49.8, `server_calls` empty, `attempts` 0, `final_text` empty | yes |
| Negatives passed on both arms with zero tool calls | autopsy close | all three negative rows, both arms, `pass` true, `attempts` 0 | yes |
| Both arms above 92% | re-run section | 96.30 and 92.59 are both above 92 | yes |
| About three more baseline misses to clear +10 pp | was in `hermes-vs-current.md` | remaining gap is 1.70 tasks. Two more misses clear +10 pp (11.11 pp). Three is not the count | no, corrected in this check |
| Labels fixed before any scored call | was in the write-up, the handoff, and the bake-off README | stamp `2026-10-19T18:00:00Z` is after `meta.started` `2026-10-19T08:33:09Z`. Same git commit as the results | no, corrected in this check |

## Like-for-like caveats

| Claim | Source | Recomputed | Match |
|---|---|---|---|
| Hermes reasoning off at `hermes_arm.py` lines 47 and 136 | handoff founder section | line 47 is `reasoning_effort: "none"`. Line 136 is `reasoning_config={"enabled": False, "effort": "none"}` | yes |
| Opencode arm does not turn thinking off | handoff, and `hermes-vs-current.md` method table "not set" | `opencode_arm.py` has no `think` or `reasoning` setting. Its config sets model, context limit, and MCP only | yes |
| `opencode run` is a process per task; Hermes is in-process `run_conversation` | handoff | `opencode_arm.py` uses `subprocess.run`. `hermes_arm.py` calls `agent.run_conversation` | yes |
| RSS row is the agent process, not the model. Model is about 23 GB and the same for both arms | both eval docs | `peak.py` documents that Ollama processes are not added to the agent peak. `ollama_ps_after_tasks[0].size` is 23396477828 bytes = 23.396 GB (10^9) = 21.790 GiB. One ps row, so both arms shared that resident size. Sampler `ollama_peak_rss_bytes` max is about 6.0 GiB (Hermes) and 6.2 GiB (opencode). That is a different measurement. The "about 23 GB" sentence matches the ps `size` in decimal GB | yes |
| README "22 GB model" / preflight "22 GiB model weight" | `examples/hermes-bakeoff/README.md`, `preflight.py` comment `MEM_FLOOR_KIB = (22 + 25) * 1024 * 1024` | design budget, not the ps measurement. 21.790 GiB is the measured weight. The report's "about 23 GB" is the decimal reading of the same integer | yes for the design comment. It is not the ps figure |
| 47 GiB pre-load gate was not reapplied because the model was already resident. MemAvailable 45.9 GiB before and 45.1 GiB after | `hermes-vs-current.md` reproduce section | `model_loaded_at_start` true. `run.py` then calls `wait_for_memory(8 GiB)` instead of `MEM_FLOOR_KIB` (47 GiB). `mem_available_before_kib` 48143456 = 45.913 GiB rounds to 45.9. After: 47294588 = 45.104 GiB rounds to 45.1. 45.9 is under 47, so a 47 GiB gate would not have returned immediately | yes |
| Scored run left the model loaded (`model_unloaded` false, `model_left_loaded` true) | handoff isolation section | both flags in `meta` | yes |
| `qwen3.6:35b` was not in `ollama ps` at session start, then this eval loaded it, and the scored run saw it already resident | handoff, `meta.session_model_note` | the note text is in `meta`. `ollama_ps_at_start` is `["qwen3.6:35b"]` and `model_loaded_at_start` is true, which matches "resident at scored-run start", not "absent at session start". The earlier absence is only the note | yes for the scored-run flags. The session-start absence is unverified beyond the note |
| No `scripts/pfy` or `pfylib/` wiring. Catalog HOLD 70-75 unchanged | handoff | `git diff --name-only b36234b..24fe672` has no `scripts/pfy` or `pfylib/` path and no entry file 070-075 | yes |

## Code facts the handoff lists as follow-ups

| Claim | Source | Recomputed | Match |
|---|---|---|---|
| `labels_written` hardcoded at `make_tasks.py` line 273 | handoff follow-up 3 | line 273 is `"labels_written": "2026-10-19T18:00:00Z"` | yes |
| Run start time recorded at the end, `run.py` line 417 | handoff follow-up 4 | line 417 is `"started": datetime.now(...)` inside the payload written after the task loop | yes |
| `aggregate`, `wilson`, and `percentile` have no tests | handoff follow-up 1, second clause | no matches for those names under `tests/` | yes |
| 14 of 20 scorer mutants survive | handoff follow-up 1, first clause | no mutant log, list, or script output in the tree | unverified |
| Offline unittest 9 OK | handoff reproduce | re-run this check: 9 tests, OK, 0.658s | yes |
| pytest `-m "not live"` 9 passed, 1 deselected | handoff reproduce | not re-run. `python3 -m pytest` fails: no module named pytest. The file has 9 `TestCase` methods and one `pytest.mark.live` function | unverified as an execution. The split in the file matches 9 + 1 |

## Unverified (not in the tree)

These stay as written. This check does not delete them and does not confirm them.

| Claim | Source | Why unverified |
|---|---|---|
| Hermes raised `ValueError` because context 32,768 is under the 64,000 minimum | `hermes-vs-current.md` method | `meta.num_ctx_note` says Hermes refuses 32768 (minimum 64000) and the scored run used 65536. The exception class and the "32,768" / "64,000" wording are not in `results.json` or the harness. The pin checkout is not in git |
| `~/.hermes` snapshot, 153 paths, diff empty. This run did not read Mark's `~/.hermes` | handoff isolation | no snapshot file in the tree |
| `~/.config/opencode` mtime stayed 2026-04-30 | handoff and the write-up | no stat record in `results.json` |
| No leftover Hermes or opencode processes. `openclaw-gateway` inactive and disabled | handoff isolation | no process listing in the tree |
| Session cleanup sent `keep_alive: 0` and `ollama ps` was empty afterwards, including 2026-10-20 03:31 and 11:19 PT | handoff isolation | `meta` says the scored run did not unload. Cleanup is described as outside `run.py`. No second ps capture is stored |
| No `qwen3.6-hermes-eval-*` tag was created | both eval docs | no tag inventory in the file. Absence from this repo is not an Ollama tag list |
| Raw `opencode run --format json` stream for `wz-06` was not retained | autopsy item 5 | the aggregate row is empty, and `./tmp/bakeoff/full1/` is not in the tree. Consistent with "not retained", not a proof of what the stream contained |
| Empty `submit_answer` / `compute_sum` `a: 0` payloads | autopsy item 2 | see the task table |
| 14 of 20 mutants | handoff | see the follow-up table |
| pytest 9 passed, 1 deselected, as a run | handoff | pytest is not installed in this check |

## History SHAs named by the handoff

| Claim | Recomputed | Match |
|---|---|---|
| Entry `03cfbec` | `03cfbec` 2026-10-19 catalog Entry 131 Hermes Agent | yes |
| Bake-off `b48d634` | `b48d634` 2026-10-19 eval commit. First commit that adds the tasks file and `results.json` | yes |
| Handoff `9b4c8f9` | `9b4c8f9` docs: Hermes eval handoff. Ancestor of this branch. `origin/main` at check time is `c0d38af`, and `9b4c8f9` is an ancestor of HEAD | yes |
| Merge of `origin/main` `09b1c16`, other parent `aed526d` | parents of `09b1c16` are `9b4c8f9` and `aed526d`. Date 2026-10-20 | yes |
| Renumber `73ff535`, founder decision `02dd0af`, review fixes `24fe672` | those commits exist, in that order, on this branch | yes |
| Cut from `origin/main` at `b36234b` (#303) | `b36234b` is an ancestor. Subject is catalog X intake 128-130 (#303) | yes |
| `#304` `a393a91` took entry 131 | `a393a91` contains `sources/entries/131-jevagentharness.md` | yes |
| Branch tip at the start of this lane | `24fe672`, then drop-in `ed1ce42` | yes |

## What this check did not do

No local model, no Ollama request, no `run.py --live`, no `scripts/pregate.sh`. Headline numbers were not rewritten. The two prose claims that disagreed with the tree were rewritten as above.
