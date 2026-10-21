# Handoff: hermes-wire (2026-10-21)

Branch `bot/hermes-wire`. Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire`. Cut from `origin/main` @ `e9365d545e52dcb7a319377c87edf32e1c7dce0a`. No PR. Do not merge from this run. Not a Feature GO.

## Head

| Commit | SHA |
|---|---|
| Tester FAIL fix (default-off test with a present Hermes, no Hermes toolsets, `/v1` base, fallback notice, scorer and bot mutant kills) | `a2cf3fc4d92065095f8d1db32b467c82b4a8b7c2` |
| Reviewer FAIL fix B1 B2 (opencode provider config, stdin closed, isolated home and cwd, E2E test) | `fb5e34d4a6f850fd04ddb01c7053f115d204ce05` |
| Write-up and re-run receipt | `3500119765269978bf9ad55f85ece064cdd24ead` |
| Bot flag (`PFY_BOT_INTERFACE`, default off) | `56961bbe0c2444012fd471ed9a632b156c3577dc` |
| Re-run harness (matched thinking, `tool_search` off) | `92431701c503cf670190796104dee1c45af65034` |
| Oracles, stamps, git rescore | `9f44be1af22ea5a5a8dba8216568d64df852dd4d` |
| Wording, speed caveat, millisecond TTFT | `e215cb8a4b51d04c78747df61aa30967a72102a8` |

Handoff commit: `43391e1f0913932a67bdfd161e0ceea47edbc8a3` (this file, on top of `3500119`). Stamp commits `dee7856`, `363eefb`, `7b80757` and the 2026-10-21 08:05 PT check commit are docs only. Status: session finished (end event, end_turn) and the branch is ready to gate. CI fix `56a65a15761c9fbc19509e149a0846a10e99fa91` adds a `HERMES_BAKEOFF_MEM_FLOOR_KIB` override so the ps-order test does not wait for the 47 GiB real-model floor on small runners. Tester and Reviewer gate the branch tip, which is the docs commit that adds this sentence; its SHA is pinned in the gate request because a commit cannot name itself.

Reviewer FAIL on `cbcd65dd92116ec7692e153600a37e5d2086da74` is answered by `fb5e34d` plus the docs commit that adds this paragraph (the new tip; same rule, its SHA is in the gate request). What changed:

- B1: `./pfy bot` passed `--model ollama/<model>` to opencode with an empty config dir, so opencode 1.18.x failed `Provider not found: ollama` and sent 0 requests. `run_opencode` now writes an `ollama` provider (`@ai-sdk/openai-compatible`, `baseURL` from `LOCAL_OPENAI_BASE_URL`, the model listed) to `tmp/bot-interface/opencode/config/opencode/opencode.json` and sets `OPENCODE_CONFIG`. The `PFY_BOT_INTERFACE=hermes` fallback uses the same path.
- B2: the child starts with `stdin=subprocess.DEVNULL`, so a non-tty caller no longer hangs until `PFY_BOT_TIMEOUT`.
- Isolation: opencode runs with `HOME`, XDG dirs, and cwd under `tmp/bot-interface/opencode/`, `OPENCODE_DISABLE_PROJECT_CONFIG=1`, and `--pure`, so the repo `opencode.json`, `~/.config/opencode`, and `~/.opencode` are not read.
- Tests: stdin pipe does not hang (fake), child env and config (fake), and a real-opencode E2E against an in-process stub server on both paths that skips with a named reason when opencode is absent. Each has a RED mutant in the run log.
- Tester FAIL on `cbcd65d` is answered by `a2cf3fc` plus the docs commit on top (new tip). Blocker: default off is now tested against a present stub Hermes (unset, empty, blank, `off`, `OpenCode` never start it; `hermes` does). Should-fixes: tests for garbage flag, driver `ok: false`, opencode nonzero, empty prompt, bad reasoning, XDG dirs; Hermes driver runs with `enabled_toolsets=[]` because approvals are off (plan doc says so); root `LOCAL_OPENAI_BASE_URL` gets `/v1`; fallback prints a stderr notice and the plan and `--help` say rc is opencode's; the live bake-off test is a unittest class with a named skip; scorer mutants M02 to M04, M08, M11, M12, M14, N26, N27 killed. Mutants now: bot 19/20 (B06 near-equivalent), scorer 29/30 (N30 equivalent). Run log Item 5.
- Real runs on nimo ollama `qwen3.6:35b` at `fb5e34d`, and again at `a2cf3fc` (default 65.1s, hermes 4.1s, fallback 11.7s, all rc 0, all `pong`, Ollama journal shows `POST /v1/chat/completions` 200 for each): default rc 0, hermes (worktree checkout) rc 0, hermes fallback rc 0, each answered `pong` and the Ollama journal shows `POST /v1/chat/completions` 200 for each. See the run log, Item 4.


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
| Suite | `TMPDIR=/home/mark/DEVELOP/pfy-mentat/tmp/hermes-wire-suite-tmp python3 -m unittest discover -s tests -t .` -> Ran 658 tests in 402.214s, OK (skipped=15), EXIT 0, at 2026-10-21 12:17 PT on `a2cf3fc` plus these docs. The one new skip is the live bake-off test, now a named unittest skip. The real-opencode E2E ran on nimo; it skips on ubuntu CI with `opencode binary not found on PATH or PFY_BOT_OPENCODE` |
| `ollama ps` | empty after the run (`keep_alive: 0` for `qwen3.6:35b`) |
| `~/.hermes` | sha256 manifest before and after the 11:32 PT and 12:09 PT real runs: 113616 paths, added 0, removed 0, changed 0. See isolation |
| `./pfy bot` real runs | done at `fb5e34d` (Item 4) and `a2cf3fc` (Item 5). Default, hermes, hermes fallback all rc 0 with Ollama requests logged |

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
- An import smoke at 00:17 PT ran the eval venv python with `HERMES_HOME` unset. Hermes treated `~/.hermes` as the home and replaced a 537-byte legacy SOUL scaffold with the pin default, and added a config backup plus cache files. Those bytes were restored from the known legacy scaffold and the eight added paths were removed. Snapshot diff after that restore: empty. sha256 compare at 2026-10-21 11:35 PT: `~/.hermes/SOUL.md` hashes to `3a10ce135b52753beda81368712decc49a83715d527e00660c19f69d1b4879da`, equal to the legacy `SOUL_EOF` heredoc in `~/.hermes/hermes-agent/scripts/install.sh` (lines 1733-1747). A full sha256 manifest of `~/.hermes` before and after the Item 4 real runs matched (added 0, removed 0, changed 0). File contents were not printed.
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
