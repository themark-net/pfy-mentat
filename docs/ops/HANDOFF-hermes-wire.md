# Handoff: hermes-wire (2026-10-21)

Branch `bot/hermes-wire`. Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire`. Cut from `origin/main` @ `e9365d545e52dcb7a319377c87edf32e1c7dce0a`. No PR. Do not merge from this run. Not a Feature GO.

## Head

| Commit | SHA |
|---|---|
| Write-up and re-run receipt | `3500119765269978bf9ad55f85ece064cdd24ead` |
| Bot flag (`PFY_BOT_INTERFACE`, default off) | `56961bbe0c2444012fd471ed9a632b156c3577dc` |
| Re-run harness (matched thinking, `tool_search` off) | `92431701c503cf670190796104dee1c45af65034` |
| Oracles, stamps, git rescore | `9f44be1af22ea5a5a8dba8216568d64df852dd4d` |
| Wording, speed caveat, millisecond TTFT | `e215cb8a4b51d04c78747df61aa30967a72102a8` |

Handoff commit: `43391e1f0913932a67bdfd161e0ceea47edbc8a3` (this file, on top of `3500119`). Stamp commit: `dee785691e1351b5f4a393e45d462d350844879a`. Tester and Reviewer gate the branch tip. A later commit that only records `dee7856` does not change the work.

## Status

| Item | Status |
|---|---|
| R1 process boundary | done. One subprocess of `hermes_arm.py` per task. `AIAgent.run_conversation` is inside that process |
| R2 "much faster" caveat | done. The 2026-10-19 line links to the not-like-for-like note |
| R3 sub-second TTFT | done. Whole-second stamps are rejected. The re-run p50 is 4.877s and 5.364s |
| Prerequisites 1 to 7 | done in `9f44be1`. RED mutants were restored. See the run log |
| Live re-run | done. Receipt `pipelines/dogfood/hermes-bakeoff/results-rerun.json`. `results.json` was not overwritten |
| `./pfy bot` flag | done. Default opencode. `PFY_BOT_INTERFACE=hermes` opts in. Plan `docs/plans/hermes-bot-interface.md` |
| Catalog | HOLD 70-75 unchanged. No rescore. No Feature GO |
| Suite | `env -u TMPDIR python3 -m unittest discover -s tests -t .` -> Ran 640 tests in 409.171s, OK (skipped=14), EXIT 0, at 2026-10-21 01:02 PT |
| `ollama ps` | empty after the run (`keep_alive: 0` for `qwen3.6:35b`) |
| `~/.hermes` | diff empty after restore (113616 paths). See isolation |

## Re-run numbers

Local `qwen3.6:35b` on Ollama. Pin `ddabd383`. opencode 1.18.32. 27 labels unchanged. Thinking off on both arms (153 proxied chat completions forced `think: false`, temperature 0, seed 1, `reasoning_effort: none`). Hermes `tool_search` off. Meta calls 0. Each Hermes task saw the six `mcp__bakeoff__*` tools. Requested `num_ctx` 65536. Observed `context_length` 262144. Started `2026-10-21T07:40:26.585Z`. `model_unloaded: true`.

| Metric | Hermes | opencode | Prior (2026-10-19) |
|---|---:|---:|---|
| Task success | 26/27 = 96.30% | 26/27 = 96.30% | 26/27 vs 25/27 |
| Wilson 95% | 81.7% to 99.3% | 81.7% to 99.3% | overlap then, overlap now |
| Valid tool-call rate | 36/36 = 100% | 36/36 = 100% | 82.61% vs 97.83% |
| p50 latency | 7.011s | 7.191s | 8.75s vs 47.38s |
| TTFT p50 | 4.877s | 5.364s | 6.44s vs 42.00s |
| Agent peak RSS | 239.8 MiB | 1.03 GiB | 221 MiB vs 1.04 GiB |

Verdict: **NO-WIN**. Task success is tied, not +10 pp. Valid rate, narrate (0), p50, and peak RSS pass. The valid-rate gap from the prior run closed. The latency gap did not survive matched thinking. The RSS gap remains. Both arms miss only `ch-ph-08-missing-ci` (one schema-valid `hold`; label `escalate`).

The verdict does not block the flag. The founder already chose Hermes.

## Wiring

`./pfy bot "prompt"` runs `pfylib/bot_interface.py`. Unset, empty, `opencode`, and `off` keep the opencode path. `hermes` uses the isolated library driver when the checkout and python exist and `PFY_HERMES_HOME` is not under `~/.hermes`. Otherwise it falls back to opencode, or exits 2 with `next: ./pfy attach opencode` when that binary is also missing. It does not run the Hermes installer and it does not exec `~/.local/bin/hermes`. Model server down exits 2 with `next: ./pfy up` and starts neither agent. A malformed tool call exits 1. Timeout kills the child process group this command started and exits 2.

Turn it off: `unset PFY_BOT_INTERFACE` or `PFY_BOT_INTERFACE=opencode`.

`./pfy attach hermes` is unchanged.

## Isolation

- Scored run `HERMES_HOME` was `tmp/hermes-home` under this worktree. `HERMES_REDACT_SECRETS=true`. `PYTHONDONTWRITEBYTECODE=1` on bake-off children.
- An import smoke at 00:17 PT ran the eval venv python with `HERMES_HOME` unset. Hermes treated `~/.hermes` as the home and replaced a 537-byte legacy SOUL scaffold with the pin default, and added a config backup plus cache files. Those bytes were restored from the known legacy scaffold (size match only) and the eight added paths were removed. Snapshot diff after that restore: empty. File contents were not printed.
- `~/.local/bin/hermes` was not used. No gateway, dashboard, API server, or cron was started by this run.
- The model was unloaded. `ollama ps` was empty at 01:02 PT.
- `openclaw-gateway.service` was inactive and disabled at 01:03 PT. This run did not start it.

## What is left

- Tester and Reviewer gate `bot/hermes-wire`. No merge from this run.
- Leave the flag off until someone sets `PFY_BOT_INTERFACE=hermes`.
- Do not start another 27-task run for this handoff. The command that already ran is `bash tmp/run-rerun.sh` in this worktree (gitignored). A later run should keep `--out` off `results.json`.
- `ollama ps` `context_length` stayed 262144. This run did not create a `qwen3.6-hermes-eval-*` tag and did not resize the loaded window.
- `ch-ph-08-missing-ci` is still a model miss on both arms.

Run log: [RUN-LOG-hermes-wire.md](RUN-LOG-hermes-wire.md). Eval write-up: [hermes-vs-current.md](../eval/hermes-vs-current.md).
