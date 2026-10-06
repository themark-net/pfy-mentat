# Local-inference bench results — Entry 089 (nimo / Ollama GPU)

**Cite (decision case set only):** [#230](https://github.com/themark-net/pfy-mentat/issues/230) · [ADR-0016](../adr/0016-jev-decision-layer.md)  
**Entry:** [089](../../sources/entries/089-local-inference-bench.md)  
**Host:** nimo (AMD Ryzen AI Max+ 395 / Radeon 8060S, Strix Halo). BIOS VRAM carve **64 GiB**. Linux MemTotal **~61 GiB**. GTT **~30 GiB**.  
**Harness:** [`examples/local-bench/bench.py`](../../examples/local-bench/bench.py) (stdlib, Ollama HTTP `http://127.0.0.1:11434`)  
**Receipt:** [`pipelines/dogfood/local-bench/receipt.json`](../../pipelines/dogfood/local-bench/receipt.json)  
**Cases:** [`data/decision-gates/laya-trial.cases.v0.json`](../../data/decision-gates/laya-trial.cases.v0.json) (same **48** labeled Choice cases as Entry 086; labels written `2026-10-06T00:00:00Z`, before those models ran)  
**Gate:** `PFY_JEV_CONF_GATE` **0.85** (margin chip, never percent-correct). Parse fail or confidence < 0.85 → escalate. No silent auto-act.  
**Verdict:** **RAN**. Catalog **HOLD 70–75**. No GUI. No BIOS/kernel/sysctl change. **Not a Feature GO.** CUA-S1-FORMS stays primary local.

This slice measured what already sits in the Ollama store on nimo. It did not download weights, did not start a new service, and did not change the decision default lane.

## Inventory (start of slice)

| Item | Value |
|------|--------|
| Hostname | nimo |
| CPU / iGPU | AMD Ryzen AI Max+ 395 / Radeon 8060S (Strix Halo) |
| Unified RAM | 128 GB; BIOS carves **64 GiB** VRAM |
| Linux `MemTotal` | 64406736 kB (~61.4 GiB) |
| Linux `MemAvailable` at start | 19.65 GiB (host already using ~41 GiB; do not starve) |
| Swap | 8.0 GiB (2.1 GiB used at start) |
| DRM sysfs | `card1` `mem_info_vram_total` **64.0 GiB**; `mem_info_gtt_total` **30.712 GiB** |
| TTM | `/sys/module/ttm/parameters/pages_limit` **8050842** pages (~30.7 GiB, matches GTT). `amdgpu.gttsize` unset. |
| Ollama | **0.30.8**, GPU path works (`PROCESSOR` 100% GPU on loaded models) |
| ROCm | 7.1.1 (`rocminfo` present). No `vulkaninfo`. |
| llama-cli | present (not used this slice) |
| Disk `/home` | ~571 GB free |
| `num_ctx` | **2048** (small KV) |
| Unload | `keep_alive: 0` between models |

Models were already in the Ollama store. The harness never pulled. `gpt-oss:120b` (~65 GB) was skipped because it exceeds the 64 GiB VRAM carve.

## Results

Accuracy is raw choice match on all ran cases (including escalated), matching Entry 086 reporting. Escalate = parse fail or `confidence < 0.85`. Wrong-but-confident (wbc) = held at/above the gate and wrong.

Baselines from Entry 086 on the **same 48** cases:

| Lane | Accuracy | Escalate | wbc |
|------|----------|----------|-----|
| CUA-S1-FORMS | 56.3% (27/48) | 22.9% (11/48) | 16 |
| laya:english | 62.5% (30/48) | 100% (48/48) | 0 |

Live Ollama numbers. Wall **2026-10-06T03:48:04Z → 03:54:11Z** (~6.1 min including stretch). `num_ctx` **2048**. MemAvailable never dropped under 8 GiB (low ~19 GiB at start; ~45 GiB after unload).

| Model | Load | `ollama ps` SIZE / PROCESSOR | VRAM used | PP tok/s | Decode tok/s | Accuracy | Escalate | wbc | Held acc |
|-------|------|------------------------------|-----------|----------|--------------|----------|----------|-----|----------|
| **qwen2.5-coder:1.5b** | 1.76 s | **1.1 GB / 100% GPU** | 1.80 GiB | **1920.8** | **117.2** | 54.2% (26/48) | **0%** (0/48) | **22** | 54.2% (26/48) |
| **glm-4.7-flash:latest** | 12.11 s | **19 GB / 100% GPU** | 18.51 GiB | 531.5 | 53.2 | 39.6% (19/48) | 33.3% (16/48) | 13 | 59.4% (19/32) |
| **qwen3-coder:30b** | 39.44 s | **18 GB / 100% GPU** | 18.25 GiB | **723.8** | **65.2** | **79.2% (38/48)** | **2.1% (1/48)** | **10** | **78.7% (37/47)** |
| **qwen3-coder-next:latest** (stretch) | 147.7 s | **52 GB / 11%/89% CPU/GPU** | 44.59 GiB | 169.2 | 17.8 | **83.3% (40/48)** | **2.1% (1/48)** | **7** | **85.1% (40/47)** |
| gpt-oss:120b | skipped | 65 GB > 64 GiB VRAM carve | — | — | — | — | — | — | — |

GPU-resident size is `ollama ps` SIZE / `size_vram` (and sysfs `mem_info_vram_used`). The harness RSS sampler on this run also matched the parent `grok` PID because the prompt text contained the words “ollama” and “runner”; treat `peak_rss_kb` in the receipt as contaminated. Stretch load was observed live at ~36 GiB `llama-server` RSS while weights streamed, then ~8 GiB RSS with **44.6 GiB** VRAM. The sampler now keys off `/proc/<pid>/exe` only.

**qwen3-coder:30b** is the required-model winner: 79.2% vs CUA 56.3% on this set, 10 vs 16 wbc, 2.1% escalate, 65 decode tok/s, 100% GPU, 18 GB. Stretch **qwen3-coder-next** is more accurate (83.3%, 7 wbc) but 3.7× slower to decode and occupies 52 GB (89% GPU). glm-4.7-flash is slower and worse here (typos like `escelate`, 33% escalate). The 1.5b is the smoke/latency floor and is fully overconfident (0% escalate, 22 wbc). These are JSON Choice prompts against coding LLMs, not a typed Jev engine.

## Recommendation (nimo, now)

- **Run `qwen3-coder:30b` as the local coding worker** — MoE Q4_K_M, 18 GB, 100% GPU, ~65 decode tok/s and ~724 PP tok/s at ctx 2048. Best required-model speed/quality on this host.
- Keep **`qwen2.5-coder:1.5b`** for smokes and tight loops (~117 decode tok/s). Do not use it as a held Choice engine (22 wbc).
- **`qwen3-coder-next:latest` is optional stretch** — fits the 64 GiB carve (52 GB, 89% GPU), 83.3% on this set, ~18 decode tok/s. Use when quality matters more than interactive tok/s. Not the default worker.
- Leave **`glm-4.7-flash`** off the default worker list on this set (39.6% accuracy, 33% escalate).
- **CUA-S1-FORMS stays the default decision lane.** This bench does not replace Jev. Not a Feature GO.
- Skip `gpt-oss:120b` until a GTT/BIOS expansion (document-only below) is approved.

## Expansion (document only — do not apply)

**Do not change BIOS, kernel cmdline, or sysctl in this slice.** Any of the knobs below needs Mark approval.

### Why the GPU pool is smaller than 128 GB

nimo is unified-memory Strix Halo. The 128 GB is physically one pool. The BIOS **VRAM carve** (UMA / Dedicated GPU Memory, currently **64 GiB**) is subtracted before Linux boots, so `MemTotal` is ~61 GiB. The amdgpu driver then publishes a **GTT** window (~30.7 GiB here) that maps remaining system RAM for the iGPU. Ollama's `100% GPU` loads in this run sat in the 64 GiB carve (`SIZE` 19 GB for the 30B-class MoEs). `gpt-oss:120b` at ~65 GB does not fit that carve.

Lowering the BIOS carve (typical community values: **512 MiB–2 GiB**, vendor minimum if 512 MiB is missing) returns that RAM to Linux `MemTotal`. Raising the TTM/GTT ceiling then lets the iGPU *map* most of the unified pool without a 64 GiB hard split. AMD's Strix Halo optimization note prefers a **small** BIOS VRAM reservation plus a larger shared TTM/GTT limit, because on this silicon there is no discrete-VRAM speed cliff. ([ROCm Strix Halo system optimization](https://rocm.docs.amd.com/en/docs-7.2.0/how-to/system-optimization/strixhalo.html), retrieved 2026-10-06.)

This run already placed `qwen3-coder-next` (52 GB, 44.6 GiB VRAM) inside the 64 GiB carve. `gpt-oss:120b` at ~65 GB still does not. A smaller BIOS carve plus a larger TTM/GTT ceiling is the path that would make 120B-class weights a GTT-backed load instead of bouncing off the carve. It is **not** free: Linux, the desktop, and other processes still need RAM. A 108–120 GiB GTT on a 128 GB box leaves a thin host margin. This host already had ~40 GiB in use before the bench.

### Typical knobs (cite, do not set)

| Knob | Where | What it does | Notes |
|------|--------|--------------|--------|
| BIOS UMA / Dedicated GPU Memory / iGPU Memory | firmware | Size of the VRAM carve subtracted from Linux `MemTotal` | Currently **64 GiB** on nimo. Community local-AI setups often drop this to 512 MiB–2 GiB. |
| `ttm.pages_limit` | kernel cmdline or `/sys/module/ttm/parameters/pages_limit` | Max 4 KiB pages TTM may map for GPU use (the real GTT ceiling) | Value is **pages**, not GB. Example: `27648000` ≈ 105 GiB. |
| `ttm.page_pool_size` | same | TTM page pool | Often set equal to `pages_limit` in community writeups. |
| `amdgpu.gttsize` | module param (MB) | Old GTT-size knob | **Deprecated**; dmesg asks you to use `ttm.pages_limit` instead ([Jeff Geerling, 2025-08-08](https://www.jeffgeerling.com/blog/2025/increasing-vram-allocation-on-amd-ai-apus-under-linux/)). |
| `amdttm.pages_limit` | Instinct-oriented name | Same idea on some kernels | Easy to mix up with `ttm.*`; confirm the live module (`/sys/module/ttm/...`). |

Worked examples (for a later approved change, not this slice):

- Geerling on Fedora / AI Max+ 395: `amdttm.pages_limit=27648000` and `amdttm.page_pool_size=27648000`, then `dmesg` showing ~108000M GTT with a small BIOS carve. ([jeffgeerling.com, 2025-08-08](https://www.jeffgeerling.com/blog/2025/increasing-vram-allocation-on-amd-ai-apus-under-linux/))
- ROCm docs: keep BIOS VRAM small (e.g. 0.5 GB) and raise TTM; default GTT is about half of visible system RAM. ([rocm.docs.amd.com Strix Halo](https://rocm.docs.amd.com/en/docs-7.2.0/how-to/system-optimization/strixhalo.html))
- Retail 128 GB Beelink profile in a 2026-10-01 setup guide: BIOS UMA **512MB** (or 2GB if that is the vendor minimum) plus `amdgpu.gttsize=131072 ttm.pages_limit=31457280` — recorded as a **limit**, not allocated VRAM. ([strixhaloguide.com](https://strixhaloguide.com/amd-strix-halo-setup/))
- Ubuntu GRUB examples using `ttm.pages_limit=33554432 ttm.page_pool_size=33554432` for 128 GB Halo, and a warning that leftover `amdgpu.gttsize` plus TTM can disagree in dmesg. ([dev.webonomic.nl](https://dev.webonomic.nl/setting-up-unified-memory-for-strix-halo-correctly-on-ubuntu-25-04-or-25-10))

Verify after any approved reboot with `dmesg | grep -E 'vram|GTT|ttm'`, `cat /sys/class/drm/card1/device/mem_info_{vram,gtt}_total`, and `cat /sys/module/ttm/parameters/pages_limit`. Do not apply 128 GB-class page limits on a 192 GB Gorgon Halo box without a separate profile.

### Current-price options (as of 2026-10-05/06)

Sourced street/list numbers for a **second** local box, or for a discrete 48 GB CUDA card. Prefer another **Strix Halo 128 GB** when the need is capacity on one machine. Buy a DGX Spark only if the workload needs CUDA.

| Box / card | Config | Price (USD) | Date / source |
|------------|--------|-------------|---------------|
| **Framework Desktop** | Ryzen AI Max+ 395, 128 GB, DIY, no SSD | **~$3,449** | [Phoronix 2026-09-30](https://www.phoronix.com/news/Framework-Desktop-Gorgon-Halo) (current 395/128GB “starts out at $3449”); [ComputingForGeeks 2026-10-02](https://computingforgeeks.com/ryzen-ai-max-395-mini-pc-comparison/) (direct, out of stock). 64 GB DIY $1,959. |
| **GMKtec EVO-X2** | Max+ 395, 128 GB | **$3,499.99** (1 TB) / **$3,649.99** (2 TB) | [ComputingForGeeks 2026-10-02](https://computingforgeeks.com/ryzen-ai-max-395-mini-pc-comparison/) Amazon recheck; [VideoCardz 2026-07-18](https://videocardz.com/newz/gmktec-evo-x2-with-128gb-ram-debuts-at-3500) for the 1 TB SKU. |
| **Minisforum MS-S1 Max** | Max+ 395, 128 GB / 2 TB | **~$3,799** (sale from ~$4,749 on the US store) | [ComputingForGeeks 2026-10-02](https://computingforgeeks.com/ryzen-ai-max-395-mini-pc-comparison/); [Digital4All / store.minisforum.com, Sep 2026](https://digital4all.ai/software/minisforum-ms-s1-max). Dual 10GbE + PCIe slot. EU list €3,999 on [minisforumpc.eu](https://minisforumpc.eu/products/minisforum-ms-s1-max-mini-pc) when fetched. |
| **NVIDIA DGX Spark** | GB10, 128 GB unified | **$4,699+** listed; 128 GB climbing toward **~$6,950**; 64 GB SKU **$4,999** (ships 2026-10-23) | [Techgenyz 2026-10-05](https://techgenyz.com/asus-ascent-gx10-vs-nvidia-dgx-spark-price/) NVIDIA US marketplace 128GB/4TB **$4,699** (out of stock); [ServeTheHome 2026-10-03](https://www.servethehome.com/nvidia-dgx-spark-64gb-launched-and-big-128gb-gb10-price-increases/); [Implicator 2026-10-04](https://www.implicator.ai/nvidia-adds-64gb-dgx-spark-at-4-999-as-128gb-model-climbs-to-6-950/). Buy Spark **only if CUDA is required**. |
| **Used RTX A6000 48 GB** | Ampere workstation, 48 GB GDDR6 | Street about **$4,399–$5,509** (median ask ~$5,000 on 2026-10-05/06) | [Silicon Comps 2026-10-05](https://siliconcomps.com/gpu/rtx-a6000/) eBay sample median **$5,000**, lowest sampled **$4,399**; [GPUDojo 2026-10-05](https://gpudojo.com/a6000) used from $4,199, IQR **$4,804–$5,509**; [RigPrice 2026-10-06](https://rigprice.com/gpu/rtx-a6000/) going rate **$5,000**. Needs a PCIe host, 300 W, CUDA. 48 GB is less capacity than Strix Halo 128 GB unified. |

**Capacity value:** a 128 GB Strix Halo mini (Framework ~$3,449 / EVO-X2 ~$3,499–$3,649 / MS-S1 Max ~$3,799) still buys more model-resident bytes than a used 48 GB A6000 (~$5k + workstation) or a DGX Spark at $4,699–$6,950. nimo is already that class. A second Halo box is the expansion that matches this bench. Spark is the CUDA tax.

## Locks respected

- Decision API, not chat. Cite **#230** only for the case set. Do not reopen #76.
- Catalog **HOLD 70–75**.
- Confidence = margin (`conf ok` / `conf low`). Gate ~0.85. No silent auto-act.
- CUA-S1-FORMS stays primary local. No TOOLS.md / `data/tools.json` row. Entry 089 stays I0 / trial-ran.
- No GUI. No Mark. No Feature GO. No BIOS/kernel/sysctl change.
