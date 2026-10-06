# atg-compile — live probe (2026-10-06)

**Branch:** `build/local-lane-atg`  
**Not a Feature GO.** Catalog HOLD 70–75. Stage is **I2**. Not I3.

Credit: Zhang et al. (2026), arXiv:2607.01942. Independent reimplementation. Not official ATG code. Not a paper-benchmark result.

## Live — Ollama `qwen3.6:35b`

Host was quiet after the atg PoC unloaded the same tag. Command:

```bash
python3 examples/atg-compile/bench.py \
  --base-url http://127.0.0.1:11434 \
  --model qwen3.6:35b \
  --case-timeout 180 \
  --atg-repo /tmp/atg-finish \
  --receipt pipelines/dogfood/atg-compile/receipt-live-qwen36-35b.json
```

Exit 0. The bench's receipt field `integration_stage` still says `I1` because the runner writes that constant. The catalog was set to I2 after this score.

| Metric | Value |
| --- | --- |
| Cases | 10 |
| Valid DAGs | 2 (`ac-01-mul-six-seven`, `ac-08-parallel-sums`) |
| Sink-correct | 2 |
| Valid-DAG rate | 0.20 |
| Repairs | 0 |
| Wall | 478 s |
| atg SHA during the score | `86d1b8905116fb7ec954ee5c4fe0d18f763b7e16` |
| bench pin after the report commit | `3c686b6cf712d3f8095e0df10f0789692814214f` |

The other eight plans failed before tools ran. Typical error: the sink dropped the parent's declared output. Token rate is not re-measured. See `docs/dogfood/LOCAL-BENCH-5-RUNTIMES.md` (Ollama decode 96.4 tok/s on this tag).

## `qwen3-coder-next`

Not loaded. The GGUF is 51,741,599,936 bytes (48.19 GiB). MemAvailable after the 35B unload was 65.3 GiB, under blob size + 25 GiB. The lane would have exited 2. No second model was started.

## What is ready for a later quiet-host pass

| Piece | Where |
|-------|--------|
| Lane | `llamacpp-nommap` in `data/eval-lanes.json` and `pfylib.hedge`. Start, `GET /v1/models`, stop, GGUF path. Refuses when MemAvailable < model size + 25 GiB (exit 2). |
| Default model | `qwen3.6:35b` on Ollama. Not this lane. |
| Opt-in | `qwen3-coder-next` via `llamacpp-nommap` only, one model at a time, after the host is quiet. |
| Bench | `examples/atg-compile/bench.py` plus `data/decision-gates/atg-compile.cases.v0.json` (10 tasks). |
| atg pin | `build/atg-finish` @ `3c686b6cf712d3f8095e0df10f0789692814214f` (this host: `/tmp/atg-finish`). The receipt names the scored parent `86d1b8905116fb7ec954ee5c4fe0d18f763b7e16`. Do not score `~/DEVELOP/atg-framework`. |

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

**Next:** coder-next only when MemAvailable covers 48.19 GiB + 25 GiB, one model, lane `llamacpp-nommap`. Do not promote past I2 from that run without a new decision. T-0127's 35B half is done.
