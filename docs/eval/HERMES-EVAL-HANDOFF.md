# Handoff: Hermes Agent bake-off (2026-10-19)

**Branch:** `bot/hermes-eval` (worktree `/home/mark/DEVELOP/pfy-mentat/tmp/hermes-eval`), cut from `origin/main` @ `b36234b` (#303). Not merged. Not a Feature GO. No production wiring. Catalog HOLD 70–75 unchanged.

**Tip:** the commit `docs: Hermes eval handoff` on this branch. Parent bake-off commit `b48d634`. Entry commit `03cfbec`.

## What shipped vs open

- **A shipped.** `sources/entries/131-hermes-agent.md`. TOOLS.md notes only. No new `data/tools.json` row. Scores not invented.
- **B shipped.** Harness `examples/hermes-bakeoff/`, tasks `data/decision-gates/hermes-bakeoff.tasks.v0.json` (27, labels before the run), results `pipelines/dogfood/hermes-bakeoff/results.json`, write-up [hermes-vs-current.md](hermes-vs-current.md).
- **C skipped.** Verdict is NO-WIN. No `docs/plans/hermes-bot-interface.md`. What would have to change for a re-run is in the eval doc.
- **D this file.** Pointer at the top of `docs/PENDING-HANDOFF.md`. Row for `hermes-eval.md` in `docs/build-dropins/README.md`.

## Verdict

**NO-WIN** on `qwen3.6:35b` (Ollama 0.30.8).

| | Hermes `AIAgent.run_conversation` `ddabd383` | `opencode run` 1.18.32 |
|---|---:|---:|
| Task success | 26/27 = 96.30% (Wilson 81.7–99.3%) | 25/27 = 92.59% (Wilson 76.6–97.9%) |
| Valid tool-call rate | 82.61% (38/46) | 97.83% (45/46) |
| Narrate rate | 0 | 0 |
| p50 latency | 8.75s | 47.38s |
| Agent peak RSS | 221 MiB | 1.04 GiB |

Failed the +10 pp success bar (+3.70 pp) and the valid-rate bar (−15.2 pp). Intervals overlap. Hermes was faster and lighter. A first scoring pass that counted Hermes `tool_search` / `tool_call` envelopes as invalid attempts said 42% valid; the published rate excludes those meta calls. NO-WIN either way. One scored pass. No second model pass.

Requested `num_ctx` 65536 after Hermes refused 32768. `ollama ps` `context_length` stayed 262144 for both arms.

## Reproduce

```bash
python3 -m unittest tests.test_hermes_bakeoff
python3 examples/hermes-bakeoff/run.py --check --base-url http://127.0.0.1:9
python3 examples/hermes-bakeoff/run.py --live --skip-ctx-probe --num-ctx 65536 \
  --work ./tmp/bakeoff/full1 \
  --out pipelines/dogfood/hermes-bakeoff/results.json
```

Offline: unittest 9 OK. pytest `-m "not live"` 9 passed, 1 deselected (`PytestUnknownMarkWarning` on `live`). The live mark stays deselected unless `HERMES_BAKEOFF_LIVE=1`.

## Isolation

- `~/.hermes` untouched: **yes**. Snapshot before install vs after cleanup, 153 paths, diff empty. This run did not read Mark's `~/.hermes` or `~/.local/bin/hermes`. `HERMES_HOME` was `./tmp/hermes-home`. `HERMES_IGNORE_USER_CONFIG` was left unset because the value `1` also skips that home's `config.yaml`.
- `~/.config/opencode` mtime stayed 2026-04-30. opencode XDG homes were under `./tmp/opencode-xdg` and per-task dirs under `./tmp/bakeoff/full1`.
- No Hermes gateway, dashboard, API server, or cron. No leftover `hermes_arm`, `opencode run`, or `mcp_server.py` from this run.
- `openclaw-gateway.service`: **inactive**, **disabled**. Not started.
- `qwen3.6:35b` was not in `ollama ps` at session start. This eval loaded it. Cleanup sent `keep_alive: 0`. `ollama ps` is empty. No `qwen3.6-hermes-eval-*` tag was created.
- `./tmp/` left in place (git-ignored), including the pin checkout and per-task transcripts.

## Blockers

None that stopped the ship. Driver bugs fixed before the scored pass, each once: Ollama tag check was calling `/v1/api/tags`; relative `--out` was written after `chdir` into the checkout; the MCP server spoke Content-Length and this pin's SDK reads newline JSON. No identical failure three times.

## Next

Tester and Reviewer gate the merge. Do not merge from this run. Do not wire `scripts/pfy` or `pfylib/`. Do not promote Hermes in the catalog. A re-run only if the question changes; the list is in [hermes-vs-current.md](hermes-vs-current.md).
