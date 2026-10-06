### Entry 092: Local-inference edge probe — OLLAMA_LOAD_TIMEOUT=30m (big MoEs)

- **URL**: harness `examples/local-bench/bench.py` (+ runner RSS fix). Results: [docs/dogfood/LOCAL-BENCH-4-EDGE.md](../../docs/dogfood/LOCAL-BENCH-4-EDGE.md). Cases cite **#230**. Stacks on Entry [091](091-local-bench-memoryhigh-85g.md) / merged #272 (`96cdc73`).
- **Date**: 2026-10-05 / 2026-10-06 night PT (nimo)
- **Source / Poster**: Mark set `OLLAMA_LOAD_TIMEOUT=30m`; accepts occasional lockups to find workable memory edge; document every stall. Concurrent atg-framework cloud build left alone.
- **Summary / Key Claims**: One-at-a-time edge probe of qwen3-coder-next (51G), gpt-oss:120b (65G), GLM-4.5-Air Q4 (~73G) under MemoryHigh=85G + 30m load timeout. Edge-probe MemAvailable floor **4 GiB** (relaxed from 16). Harness fix: measure **ollama-user llama-server RSS** via cmdline/comm when `/proc/pid/exe` is EACCES (Entry 091 `peak_rss_kb` ~22 MB was the wrong process). Outdir unit tests call harness helpers. Catalog HOLD. Not a Feature GO.
- **Status**: **I0 / trial-ran / no promotion**. coder-next DROP (30m timeout, never ready); gpt-oss/Air deferred. Workable edge ~22 GB. Not a Feature GO. See LOCAL-BENCH-4-EDGE.md workable-edge table + atg guidance.
