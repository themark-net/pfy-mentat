# Local-inference bench 2 — post BIOS/GTT carve (Entry 090 / #230 cases)

**Cite (decision case set only):** [#230](https://github.com/themark-net/pfy-mentat/issues/230) · Entry [089](../../sources/entries/089-local-inference-bench.md) · Entry [090](../../sources/entries/090-local-bench-post-carve.md)  
**Host:** nimo after Mark's 2026-10-05 ~9:29pm PT change: BIOS VRAM carve **16 GiB**, `ttm.pages_limit=25165824` (~96 GiB), `ttm.page_pool_size=27262976`. Linux `MemTotal` **~107 GiB**. GPU can address ~112 GiB (16+96); weight+KV budget target **≤ ~90 GB**.  
**Harness:** [`examples/local-bench/bench.py`](../../examples/local-bench/bench.py) (path bugfix: resolve `outdir` / `relative_to`).  
**Receipt:** [`pipelines/dogfood/local-bench-2/receipt.json`](../../pipelines/dogfood/local-bench-2/receipt.json)  
**Cases:** same 48 / gate **0.85**. Catalog **HOLD 70–75**. **Not a Feature GO.** CUA-S1-FORMS stays primary local.

## Inventory delta

| Item | Entry 089 (pre) | This slice (post) |
|------|-----------------|-------------------|
| BIOS VRAM carve | 64 GiB | **16 GiB** |
| GTT (`mem_info_gtt_total`) | ~30.7 GiB | **96 GiB** |
| Linux MemTotal | ~61 GiB | **~107 GiB** |
| MemAvailable at start | ~20 GiB | **~95 GiB** |
| `ollama.service` MemoryHigh | 40G (sysadmin 2026-09-19) | **still 40G** (unchanged) |

**Critical:** Ollama remains under systemd `MemoryHigh=40G` (`/etc/systemd/system/ollama.service.d/cpu-guardrails.conf`). Loads that need ≫40 GiB RSS hang/throttle even though GTT is 96 GiB. System `llama-cli` on PATH exposes **CPU-only** ggml backends (no ROCm/Vulkan device list), so bypassing Ollama for GPU is not available without a new build/toolbox (out of scope / would need Mark).

## Research shortlist (Oct 2026) — verified sources

MoE / low-active preferred for ~256 GB/s Strix Halo bandwidth. Fit = weights at a sensible Q3/Q4 ≤ ~90 GB **and** runnable under current Ollama MemoryHigh unless noted.

| Model | Total / active | Quant / size | Fits 90 GB weights? | Runs under Ollama MemoryHigh=40G? | Source |
|-------|----------------|--------------|---------------------|-----------------------------------|--------|
| **qwen3-coder:30b** (incumbent) | ~30.5B MoE / ~3B | Q4_K_M **18 GB** | yes | **yes** | [ollama.com/library/qwen3-coder](https://ollama.com/library/qwen3-coder); Entry 089 |
| **qwen3.6:35b** | ~35B MoE / ~3B A3B | Q4 ~**23–24 GB** | yes | **yes** | [ollama.com/library/qwen3.6](https://ollama.com/library/qwen3.6); [HF Qwen3.6-35B-A3B](https://huggingface.co/Qwen) community notes ~3B active |
| **qwen3-coder-next:latest** | ~80B-class / low active | Q4_K_M **51 GB** | yes | **no** (hung cold load) | local store; [strixhaloguide evidence](https://strixhaloguide.com/evidence/) ~59 tg/s class |
| **gpt-oss:120b** | 116.8B MoE / ~5.1B | MXFP4 **65 GB** | yes | **no** (≫40G) | [ollama.com/library/gpt-oss](https://ollama.com/library/gpt-oss); Apache-2.0 |
| **nemotron-3-super:120b** | 120B / 12B active | **87 GB** | yes (tight) | **no** | [ollama.com/library/nemotron-3-super](https://ollama.com/library/nemotron-3-super); pull aborted (~5h ETA at ~5 MB/s) |
| **GLM-4.5-Air** | **106B / 12B** MoE | Q4_K_M **~73.5 GB** | **yes** | **no** (≫40G) | [z.ai GLM-4.5 docs](https://docs.z.ai/guides/llm/glm-4.5); [bartowski GGUF Q4_K_M 73.50GB](https://huggingface.co/bartowski/zai-org_GLM-4.5-Air-GGUF); Ollama community `MichelRosselli/GLM-4.5-Air:Q4_K_M` |
| **glm-4.7-flash** | ~29.9B MoE / ~3B | Q4_K_M **19 GB** | yes | **yes** | [ollama.com/library/glm-4.7-flash](https://ollama.com/library/glm-4.7-flash); already local |
| **GLM-5.3-Flash** | **320B / 18B** MoE | Q4 ~**176–200 GB**; Q2_K ~**106–114 GB** | **no** (even Q2 ≥106 GB >90) | n/a | [z.ai blog](https://z.ai/blog/glm-5.3-flash); [batiai GGUF sizes](https://huggingface.co/batiai/GLM-5.3-Flash-GGUF); Ollama **cloud-only** ([library/glm-5.3-flash](https://ollama.com/library/glm-5.3-flash)) |
| **GLM-4.6** (full) | ~355–357B / ~32B | Q4 ≫90 GB; Ollama often cloud | **no** | n/a | [z.ai GLM-4.6](https://docs.z.ai/guides/llm/glm-4.6); [HF zai-org/GLM-4.6](https://huggingface.co/zai-org/GLM-4.6). **No GLM-4.6-Air** released as of 2026-10-05 |
| **GLM-5.3-Flash** extreme 1-bit | 320B / 18B | Unsloth UD-IQ1_S **~93 GB** | borderline file size; **not usable quality** for this harness | n/a | [unsloth GLM-5.3-Flash](https://unsloth.ai/docs/models/glm-5.3-flash) — treat as research only; prefer not to chase |
| **GLM-4.5** (full) | 355B / 32B | Q4 ≫90 GB | **no** | n/a | [z.ai GLM-4.5](https://docs.z.ai/guides/llm/glm-4.5) |
| **GLM-5** | 744B / 40B | retired on Ollama library; enormous | **no** | n/a | [ollama.com/library/glm-5](https://ollama.com/library/glm-5) (retired 2026-07-15) |
| **DeepSeek-V4-Flash** | 284B / 13B | retired on Ollama; UD-IQ2 ~91 GB | borderline / retired | n/a | [ollama deepseek-v4-flash retired](https://ollama.com/library/deepseek-v4-flash); [strixhaloguide models](https://strixhaloguide.com/strix-halo-models/) |

Community Strix Halo speed context (not re-measured here): [strixhaloguide.com/evidence](https://strixhaloguide.com/evidence/), [kyuz0 toolboxes](https://github.com/kyuz0/amd-strix-halo-toolboxes), [llm-tracker Strix Halo](https://llm-tracker.info/_TOORG/Strix-Halo).

## GLM-4.7-flash autopsy (why 39.6% before)

**Not** a thinking-token / JSON fence failure. All **48/48** `parse_ok`. Raw replies were valid JSON. Failures were **instruction-following on Choice keys**:

- Typo keys: `escelate` (for `escalate`), `truncat` (for `truncate`), `skipskip`, `fre token`
- Invented keys: `none`, `default_if_unanswered`, `implemented`, …

Typo-normalized replay (map obvious typos → canonical keys only): accuracy **54.2%**, escalate **37.5%**, wbc **7**, with **15** typo fixes. Still below CUA (56.3%) and far below `qwen3-coder:30b` (79.2%). **Do not promote glm-4.7-flash** as a decision or coding worker on this set.

Best-fitting **local** GLM that Mark's chatter likely means: **GLM-4.5-Air Q4 (~73 GB)** — blocked today by Ollama `MemoryHigh=40G`, not by the new GTT.

## Results (measured this slice)

| Model | Load | Size / processor | PP tok/s | Decode | Accuracy | Escalate | wbc | Notes |
|-------|------|------------------|----------|--------|----------|----------|-----|-------|
| **qwen3-coder:30b** (re-run) | (warm path) | 18 GB / 100% GPU | **1154** | **74.9** | **79.2% (38/48)** | **2.1%** | **10** | Faster PP vs Entry 089 (724→1154) after carve |
| **glm-4.7-flash:latest** | ~12 s class | 19 GB / 100% GPU | 639 | 53.3 | 39.6% | 33.3% | 13 | Same pattern as 089; typos/invented keys |
| **qwen3.6:35b** | cold+cases | **22 GB** Q4_K_M / 100% GPU | **807.6** | **94.9** | **79.2% (38/48)** | **0.0%** | **10** | Tied accuracy with 30b; faster decode; 0 escalate |
| qwen3-coder-next | — | 51 GB | — | — | — | — | — | **Blocked** MemoryHigh=40G |
| gpt-oss:120b | — | 65 GB | — | — | — | — | — | **Blocked** MemoryHigh=40G |
| GLM-4.5-Air Q4 | — | ~73 GB | — | — | — | — | — | **Blocked** MemoryHigh=40G |

Baselines (same cases): CUA 56.3% / 22.9% esc / 16 wbc; Laya english 62.5% / 100% esc / 0 wbc.

## Recommendation

### On nimo **now** (no further Mark action)

- **Coding worker:** prefer **`qwen3.6:35b`** (79.2% / 0% esc / ~95 decode tok/s); **`qwen3-coder:30b`** remains co-equal on accuracy with higher PP (~1154) if vision/tool quirks appear.
- **Decision lane:** keep **CUA-S1-FORMS**. Do not route typed decisions through glm-4.7-flash.
- **`qwen3.6:35b` measured:** same **79.2%** accuracy as 30b, **0%** escalate (vs 2.1%), decode **~95 tok/s** (vs ~75). Prefer **`qwen3.6:35b`** as coding worker for throughput; keep 30b as fallback.

### Needs **Mark approval**

1. **Raise or remove `ollama.service` `MemoryHigh=40G`** (sysadmin drop-in from 2026-09-19) now that BIOS carve is 16 GiB and GTT is 96 GiB — otherwise the new memory map cannot host gpt-oss:120b, qwen3-coder-next, or **GLM-4.5-Air**. Suggested trial: `MemoryHigh=96G` (or infinity) with Kronos Nice/CPUWeight kept. Reversible by restoring the drop-in.
2. Optional: vendor a ROCm/Vulkan `llama.cpp` toolbox (e.g. kyuz0) if we want GPU outside Ollama's cgroup.
3. Do **not** chase GLM-5.3-Flash locally until weights ≤90 GB exist (current Q2 still ~106 GB+).

## Locks

- Cite #230 only for cases. Catalog HOLD 70–75. No Feature GO. No BIOS/kernel/sysctl changes in this slice. No committed `*.log` / grok-home / weights.
