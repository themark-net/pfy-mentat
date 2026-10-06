# atg-compile — live not run (2026-10-06)

**Branch:** `build/local-lane-atg`  
**Not a Feature GO.** Catalog HOLD 70–75. Stage stays **I1**. Not I2.

## Live

Not run. The host was not quiet: a parent session had `qwen3.6:35b` loaded in Ollama and was running a PoC. This slice did not call Ollama, did not start `llama-server`, and did not start vLLM.

No live valid-DAG rate, sink-correct rate, repair count, or wall time is recorded here. Do not treat the offline fake-server receipt as a model score.

## What is ready for the quiet-host pass

| Piece | Where |
|-------|--------|
| Lane | `llamacpp-nommap` in `data/eval-lanes.json` and `pfylib.hedge`. Start, `GET /v1/models`, stop, GGUF path. Refuses when MemAvailable < model size + 25 GiB (exit 2). |
| Default model | `qwen3.6:35b` on Ollama. Not this lane. |
| Opt-in | `qwen3-coder-next` via `llamacpp-nommap` only, one model at a time, after the host is quiet. |
| Bench | `examples/atg-compile/bench.py` plus `data/decision-gates/atg-compile.cases.v0.json` (10 tasks). |
| atg pin | `build/atg-finish` @ `86d1b8905116fb7ec954ee5c4fe0d18f763b7e16` (this host: `/tmp/atg-finish`). Do not score `~/DEVELOP/atg-framework`. |

Credit: Zhang et al. (2026), arXiv:2607.01942. This is an independent reimplementation, not official ATG code, and not a paper-benchmark result.

## Offline evidence (not a live score)

| Check | Result |
|-------|--------|
| Fake `/v1/chat/completions`: first reply malformed DAG, second valid | Receipt `n_valid=1`, `n_invalid=1`, `n_sink_correct=1`, repairs 0, exit 0 |
| Endpoint down | Exit 2, next-step message, no receipt, no driver left |
| Injected MemAvailable 1.000 GiB | `llamacpp-nommap` exit 2, server not spawned |
| `python3 -m unittest discover -s tests -t .` | 179 tests, OK, 2 skipped |
| `make eval-structural` | PASS (includes those 179 tests) |
| `python3 scripts/catalog_check.py` | PASS, `n_json=7` |
| atg pin, offline, dirty worktree | pytest **40 passed, 1 deselected**; toy `mock total={'value': 25} waves=2 parallel=2` |

**Next:** when `ollama ps` is empty and nothing else holds a model, run the bench once on `qwen3.6:35b`, then once on coder-next through the lane. Write the numbers in this file. T-0127.
