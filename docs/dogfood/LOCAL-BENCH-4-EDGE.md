# Local-bench 4 — workable memory edge on nimo (Entry 092 / #230)

**Cite:** [#230](https://github.com/themark-net/pfy-mentat/issues/230) · Entry [091](../../sources/entries/091-local-bench-memoryhigh-85g.md) · Entry [092](../../sources/entries/092-local-bench-edge-probe.md)  
**Stacks on:** #272 (`96cdc73`).  
**Env (verified):** `OLLAMA_LOAD_TIMEOUT=30m`, `MemoryHigh=85G`, Ollama 0.30.8, ~107 GiB RAM, 16 GiB VRAM, ~96 GiB GTT, **8 GiB swap**.  
**Mode:** edge probe (MemAvailable floor **4 GiB**); Mark accepts documented lockups/stalls. One model at a time. atg-framework cloud build left alone.  
**Receipt:** [`pipelines/dogfood/local-bench-4/receipt.json`](../../pipelines/dogfood/local-bench-4/receipt.json)  
**Not a Feature GO.** Catalog HOLD 70–75.

## Thesis

Ollama defaults were holding ~51 GB weights **twice** (mmap → host page cache/RSS **and** GTT copy). That is a **loader artifact**, not the Strix Halo hardware limit. This slice adds a **no-double-load** path via Ollama-bundled `llama-server` + ROCm HIP with `--no-mmap`.

## No-double-load path (cited)

| Knob | Value | Source |
|------|-------|--------|
| Binary | `/usr/local/lib/ollama/llama-server` | System `/usr/bin/llama-server` is CPU-only |
| `GGML_BACKEND_PATH` | `.../rocm_v7_2/libggml-hip.so` (**file**, not dir) | Required for ROCm0 discovery |
| `HSA_OVERRIDE_GFX_VERSION` | `11.5.1` | Strix Halo |
| `GGML_CUDA_ENABLE_UNIFIED_MEMORY` | `1` | Symbol in `libggml-hip.so` (CUDA-compat name on HIP) |
| `GGML_HIP_UMA` | `1` | Also set (belt-and-suspenders) |
| Flags | `--no-mmap -ngl 999 -c 4096 -np 1 -fa on` | Confirmed via `llama-server --help` on this build |
| Ollama `options.use_mmap` | `false` | API accepts (HTTP 200 on tiny model). Not re-benched at 51 GB under Ollama this slice |

Scripts: `run_nommap_server.sh`, `bench_llamacpp.py`, `peak_sampler.py`.

## Probe results

### A) Ollama defaults (prior this PR)

| Model | Size | MemAvail before | Runner RSS peak | GTT | Swap | Outcome |
|-------|------|-----------------|-----------------|-----|------|---------|
| **qwen3-coder-next** | 51 GB | 88.2 GiB | **~42.5 GiB** | **~48.3 GiB** | ~7.9/8 | **DROP — timeout 30m** never ready |
| gpt-oss:120b | 65 GB | — | — | — | — | deferred (contention) |
| GLM-4.5-Air Q4 | ~73 GB | — | — | — | — | deferred (pull) |

### B) llama-server ROCm `--no-mmap` (this slice)

| Model | Size | Load→healthy | Peak RSS | Peak GTT | Steady GTT | Swap peak | MemAvail min | PP p50 | Decode p50 | Choice (gate 0.85) | Outcome |
|-------|------|--------------|----------|----------|------------|-----------|--------------|--------|------------|--------------------|---------|
| **qwen3-coder-next** | 51 GB | **~132 s** | **53.7 GiB (~1×)** | 24.9† | **~0.3** | 8.0/8 | 17.5 GiB | **351** | **44.2** | acc **83.3%**, held **85.1%**, esc **2.1%**, wbc **7**, parse 48/48 | **RAN** |
| **gpt-oss:120b** | 65 GB | **~239 s** | **62.0 GiB (~1×)** | 1.3 | **~1.3** | 8.0/8 | 10.8 GiB | **262** | **30.8** | acc **43.8%**, held **84%**, esc **47.9%**, parse **26/48** | **RAN (memory)** / weak Choice JSON |
| **GLM-4.5-Air Q4** | ~73 GB | — | — | — | — | — | — | — | — | — | **SKIP** — pull incomplete (~68/72 GB partial); resume ETA ~1h; no complete HF GGUF on host |

† Peak GTT 24.9 during coder-next load was **openclaw glm-4.7-flash@128k** competition; that runner then vanished (`glm_gone`). Steady-state no-mmap GTT ≈ 0.3 GiB under UMA (weights stay in process RSS, not a second GTT copy).

## Workable edge table

| Path | Reliable max size / ctx | What tipped over |
|------|-------------------------|------------------|
| **Ollama defaults** | **~22 GB** (`qwen3.6:35b`) / ~18 GB (`qwen3-coder:30b`) @ ctx 2048 | **51 GB** double-hold (RSS+GTT) → swap thrash → never ready in 30m |
| **llama-server `--no-mmap` + UMA** | **51 GB** coder-next @ ctx **4096** (Choice OK) | **65 GB** loads & runs but Choice format weak; **73 GB** GGUF not on disk; load still fills **8 GiB swap** if host not quiet (openclaw / other GTT users) |

**Real edge:** hardware can host **~51–65 GB once** with no-mmap/UMA. The prior “22 GB edge” was the Ollama mmap+GTT double-load ceiling, not Strix Halo.

## Stalls (documented)

See [`stalls.json`](../../pipelines/dogfood/local-bench-4/stalls.json).

1. **openclaw glm@128k** — gateway kept `glm-4.7-flash` at `-c 128000`; mark cannot SIGKILL ollama-user runners (no passwordless sudo); `ollama stop` returned 0 but runner stayed. Recovery: `kill -STOP` openclaw during probe; pressure from coder-next load cleared glm GTT; `kill -CONT` after.
2. **Swap exhaustion during load** — both 51 GB and 65 GB no-mmap loads hit swap 8/8 briefly; recovered once healthy. Accept for edge-finding.

## Recommendation / atg-framework

| Role | Model |
|------|-------|
| Coding worker (safe default) | **`qwen3.6:35b`** |
| Coding fallback | **`qwen3-coder:30b`** |
| Stretch coding (no-mmap path only) | **`qwen3-coder-next`** via `llama-server --no-mmap` (not Ollama default load) |
| Decision lane | **CUA-S1-FORMS** |

**Do not** point atg at Ollama-default loads of coder-next / gpt-oss / GLM-Air. **Do not** use gpt-oss for typed #230 Choice (parse/escalate failure). Pause openclaw 128k loads before big probes. Optional Mark follow-up: more than 8 GiB swap; passwordless ops to stop stuck ollama runners.

## Harness fixes (Reviewer #272 nits — retained)

1. Runner RSS via argv0/comm when `/proc/pid/exe` is EACCES.  
2. Outdir tests call `resolve_outdir` / `log_path_for_receipt`.
