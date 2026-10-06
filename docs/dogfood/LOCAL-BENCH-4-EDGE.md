# Local-bench 4 — workable memory edge on nimo (Entry 092 / #230)

**Cite:** [#230](https://github.com/themark-net/pfy-mentat/issues/230) · Entry [091](../../sources/entries/091-local-bench-memoryhigh-85g.md) · Entry [092](../../sources/entries/092-local-bench-edge-probe.md)  
**Stacks on:** #272 (`96cdc73`).  
**Env (verified):** `OLLAMA_LOAD_TIMEOUT=30m`, `MemoryHigh=85G`, Ollama 0.30.8, ~107 GiB RAM, 16 GiB VRAM, ~96 GiB GTT.  
**Mode:** edge probe (MemAvailable floor **4 GiB**); Mark accepts documented lockups/stalls. One model at a time. atg-framework cloud build left alone.  
**Receipt:** [`pipelines/dogfood/local-bench-4/receipt.json`](../../pipelines/dogfood/local-bench-4/receipt.json)  
**Not a Feature GO.** Catalog HOLD 70–75.

## Harness fixes (Reviewer #272 nits)

1. **Runner RSS:** `/proc/<pid>/exe` is **EACCES** for ollama-user `llama-server`. Harness now matches **argv0 / comm** so PeakSampler records real runner RSS (~40 GiB), not the ~22 MB client process seen in Entry 091 receipts. Field `peak_runner_rss_gib` added. Edge probe logs `runner_rss` every sample.
2. **Outdir tests:** call `resolve_outdir()` / `log_path_for_receipt()` — no copied path logic.

## Probe log (per run)

| Model | Quant/size | ctx | MemAvail before | Runner RSS peak | Swap peak | GTT used | Load wall | Outcome |
|-------|------------|-----|-----------------|-----------------|-----------|----------|-----------|---------|
| **qwen3-coder-next:latest** | Q4_K_M **51 GB** | 2048 | **88.201 GiB** | **~42.5 GiB** (edge-events) | **~7.9 / 8 GiB** | **~48.3 GiB** | **2000 s** | **timeout** — never became available within 30m load timeout |
| gpt-oss:120b | 65 GB | 2048 | — | — | — | — | — | **deferred: host contention** (MemAvailable ~70 GiB &lt; 65+25 margin after prior stall + openclaw glm@128k) |
| GLM-4.5-Air Q4 | ~73 GB | 2048 | — | — | — | — | — | **deferred: host contention** (pull paused; not resumed) |

No 8k/16k KV headroom trial — no big model reached RAN.

## Workable edge table

| Class | Max size that ran reliably | ctx | Notes |
|-------|----------------------------|-----|-------|
| **Reliable local coding** | **~22 GB** (`qwen3.6:35b`) / **~18 GB** (`qwen3-coder:30b`) | 2048 | Entry 090/091 Choice metrics |
| **Attempted, never ready** | **51 GB** (`qwen3-coder-next`) | 2048 | Fills GTT (~48 GiB) + ~40 GiB RSS; swap thrash; `llm server loading model` / `not responding` for full **30m** |
| **Not started this slice** | 65–73 GB | — | Deferred under size+25 GiB clear-margin rule after tip-over |

**What tipped over:** not MemoryHigh=85G (cgroup allowed the load). Tip-over is **ready-state**: llama-server never answers within `OLLAMA_LOAD_TIMEOUT=30m` while swap is exhausted. Longer timeout alone did not fix coder-next.

## Recommendation

| Role | Model |
|------|-------|
| Coding worker | **`qwen3.6:35b`** |
| Coding fallback | **`qwen3-coder:30b`** |
| Decision lane | **CUA-S1-FORMS** |

### atg-framework

Point local coding at **`qwen3.6:35b`** (fallback **`qwen3-coder:30b`**). Decision via **CUA-S1-FORMS**. Avoid `qwen3-coder-next`, `gpt-oss:120b`, GLM-4.5-Air, and `glm-4.7-flash` until a ready-path exists (more swap / ROCm llama.cpp toolbox / quieter host without openclaw 128k loads).

## Mark follow-ups (optional)

- More swap than 8 GiB, or pause openclaw during big loads.
- Vendor ROCm/Vulkan llama.cpp outside ollama cgroup/start-wait.
- Do **not** expect 30m timeout alone to unlock 51GB+ on current path.
