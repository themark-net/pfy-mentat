# Local-inference bench 3 — MemoryHigh=85G unlock (Entry 091 / #230 cases)

**Cite (decision case set only):** [#230](https://github.com/themark-net/pfy-mentat/issues/230) · Entry [090](../../sources/entries/090-local-bench-post-carve.md) · Entry [091](../../sources/entries/091-local-bench-memoryhigh-85g.md)  
**Stacks on:** Entry 090 / PR #271 (merged `357e3c6`).  
**Host:** nimo — BIOS VRAM carve **16 GiB**, GTT **~96 GiB**, Linux MemTotal **~107 GiB**.  
**Ollama cgroup:** Mark raised `MemoryHigh` to **85G** (`91268055040` bytes); `MemoryMax=infinity`.  
**Harness:** [`examples/local-bench/bench.py`](../../examples/local-bench/bench.py) — `parse_ok` in decision summary; relative `--outdir` safe; **MemAvailable floor 16 GiB** (raised after nimo lockup).  
**Receipt:** [`pipelines/dogfood/local-bench-3/receipt.json`](../../pipelines/dogfood/local-bench-3/receipt.json)  
**Cases:** same 48 / gate **0.85**. Catalog **HOLD 70–75**. **Not a Feature GO.**

## Goal vs outcome

Attempt to bench the three models blocked under the old `MemoryHigh=40G`, plus optional `qwen3.6:35b` incumbent re-check.

| Model | Attempted? | Outcome |
|-------|------------|---------|
| qwen3-coder-next:latest (51 GB) | yes (3× cold load) | **DROP** — ollama `timed out waiting for llama-server to start` (~8–10 min); third attempt **aborted** after Mark reported nimo lockup (~11:05pm PT) → **deferred: host contention** |
| gpt-oss:120b (65 GB) | yes (1×) | **DROP** — same start timeout (~505 s) with MemAvailable **95.485 GiB** at start; not retried → **deferred: host contention** |
| MichelRosselli/GLM-4.5-Air:Q4_K_M (~73 GB) | pull started then stopped (~2% / 72 GB) | **SKIP** — **deferred: host contention**; not restarted (would need ~25+73 GiB clear margin + likely longer `OLLAMA_LOAD_TIMEOUT`) |
| qwen3.6:35b (22 GB) | yes | **RAN** |

## Inventory (reconciled with receipt)

| Item | Value | Source |
|------|-------|--------|
| MemoryHigh | **85G** (`91268055040`) | `systemctl show ollama`; receipt `inventory.ollama_memory_high` |
| MemoryMax | infinity | systemctl |
| MemTotal | ~107.42 GiB | receipt / `free` |
| MemAvailable at gpt-oss start | **95.485 GiB** | receipt-gpt-oss `inventory_before` |
| MemAvailable at qwen3.6 start | **55.085 GiB** | receipt-qwen36 (openclaw had also loaded glm-4.7-flash @ 128k ctx) |
| MemAvailable at coder-next attempt 3 start | **96.631 GiB** | log / stdout |
| `/home` free (pre-pull) | ~583 GiB | disk gate OK |

## Results (measured)

| Model | Size | Load wall s | MemAvail before | PP tok/s | Decode | Acc | Esc | wbc | parse_ok | Verdict |
|-------|------|-------------|-----------------|----------|--------|-----|-----|-----|----------|---------|
| **qwen3.6:35b** | **22 GB** | **45.88** | **55.085 GiB** | **88.7** | **25.2** | **79.2% (38/48)** | **0.0%** | **10** | **48/48** | **RAN** |
| qwen3-coder-next:latest | 51 GB | — | 70.2 / 85.6 / 96.6 | — | — | — | — | — | — | **DROP** (start timeout / aborted) |
| gpt-oss:120b | 65 GB | — | **95.485 GiB** | — | — | — | — | — | — | **DROP** (start timeout ~505s) |
| GLM-4.5-Air Q4 | ~73 GB | — | — | — | — | — | — | — | — | **SKIP** deferred |

**Entry 090 baseline (quiet host) for qwen3.6:35b:** PP ~808 / decode ~95 / same 79.2% / 0% esc. This slice’s tok/s are **contention-degraded** (openclaw glm-4.7-flash @ 128k + later atg-framework Grok Build) — accuracy still matches.

Baselines: CUA-S1-FORMS 56.3% / 22.9% esc / 16 wbc; Entry 090 qwen3-coder:30b 79.2% / 2.1% esc / ~75 decode.

## Was 85G MemoryHigh enough?

**For the cgroup ceiling: yes.** 51 GB and 65 GB loads were *attempted* under MemoryHigh=85G without the old 40G hang. RSS/GTT filled (e.g. coder-next ~40 GB RSS + ~48 GiB GTT).  

**For a successful ready-state: not sufficient alone.** Ollama’s internal **llama-server start timeout** (~8–10 min) fired before the runner became healthy; swap thrash (7+ GiB used) during GTT fill was common. **Mark approval:** raise `OLLAMA_LOAD_TIMEOUT` (e.g. 30m) in the ollama drop-in, then rebench **one model at a time** with MemAvailable floor **16 GiB**.

## Interference / safety

- **openclaw-gateway** loaded `glm-4.7-flash:latest` at **num_ctx=128000** mid-slice.
- Mark reported **nimo lockup ~11:05pm PT**; concurrent **atg-framework Grok Build** left undisturbed.
- Safety raised mid-slice: abort under **16 GiB** MemAvailable; do not start a big model unless MemAvailable ≳ size+25 GiB; one model at a time.

## Recommendation

| Role | Point at | Notes |
|------|----------|-------|
| **Coding worker (local)** | **`qwen3.6:35b`** | Best measured Choice accuracy among runnable models (79.2%, 0% esc, parse_ok 48). Prefer quiet host for tok/s. |
| Coding fallback | `qwen3-coder:30b` | Entry 090: same acc, higher PP when quiet. |
| **Decision lane** | **CUA-S1-FORMS** | Unchanged. No big MoE completed a Choice run this slice. |
| Avoid for now | `glm-4.7-flash`, `gpt-oss:120b`, `qwen3-coder-next`, GLM-4.5-Air | 4.7-flash weak on #230; others blocked on load-timeout / deferred. |

### Models to point **atg-framework** at

1. **Local coding:** `qwen3.6:35b` (primary), `qwen3-coder:30b` (fallback).  
2. **Local decision:** keep **CUA-S1-FORMS** via `./pfy decision` (not an Ollama weight tag).  
3. **Do not** point atg at `glm-4.7-flash:latest` for typed Choice; do not expect `gpt-oss:120b` / `qwen3-coder-next` / GLM-4.5-Air until load-timeout + quiet-host rebench.

## Locks

Cite #230 only. Catalog HOLD 70–75. No Feature GO. No BIOS/kernel/sysctl edits in-bot. No committed `*.log` / weights / build dirs. Do not disturb concurrent atg-framework Grok Build.
