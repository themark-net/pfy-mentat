# Local-bench 5 — GLM-Air score + runtime matrix (Entry 094 / #230)

**Cite:** [#230](https://github.com/themark-net/pfy-mentat/issues/230) · stacks merged #273 (`e009030`)  
**Host:** nimo · Ollama 0.30.8 · MemoryHigh=85G · ~107 GiB RAM · 8 GiB swap · OpenClaw gateway **disabled** by Mark  
**Not a Feature GO.** Catalog HOLD.

## 1) GLM-4.5-Air (priority)

| Item | Value |
|------|-------|
| Blob | `sha256-a6a5f1eb…` **72857521088 bytes** (= registry layer size; still named `-partial` on disk but **complete**) |
| Path | llama-server ROCm `--no-mmap -ngl 999 -c 4096 -np 1 -fa on` (+ `-rea off` rebench) |
| Load | **136–183 s** to healthy |
| Peak RSS | **~68.5 GiB (~1×)** · GTT ~0.35 · swap peak **8/8** · MemAvailable min **~15.7 GiB** |
| PP / decode p50 | ~500 / ~21 tok/s |
| Choice (gate 0.85) | **parse_ok 0/48, accuracy 0%, escalate 100%** (both with and without `-rea off`) |
| Raw sample | Forced-JSON prompt → content of only **`G` repeated** (degenerate) |
| Load warnings | Many `unused tensor blk.46.*` ignored |

### Correction for Mark

**GLM-Air is not the stronger #230 Choice model on this stack.** Memory path works; generation quality does not. Prefer **`qwen3.6:35b`** (79.2%) or no-mmap **`qwen3-coder-next`** (83.3% from Entry 092).

## 2) Runtime matrix — `qwen3.6:35b` (48 cases, gate 0.85, ctx 4096)

| Backend | Load | PP p50 | Decode p50 | Acc | parse | esc | wbc | Peak RSS | Notes |
|---------|------|--------|------------|-----|-------|-----|-----|----------|-------|
| **Ollama** | **16.9 s** | **791** | **96.4** | **79.2%** | 48 | 0% | 10 | 20.5 GiB | GTT ~20.7 (mmap path) |
| **llama.cpp ROCm** `--no-mmap -rea off` | **10 s** | **607** | **57.2** | **79.2%** | 48 | 0% | 10 | 20.5 GiB | Same Choice as Ollama; need `-rea off` |
| **llama.cpp Vulkan** `--no-mmap -rea off` | **15 s** | **219** | **33.1** | **77.1%** | 48 | 0% | 11 | 24.7 GiB | Slower; slightly worse acc |
| Lemonade | — | — | — | — | — | — | — | — | **SKIP** — no downloaded models; `load` starts ~16 GB pull |
| vLLM | — | — | — | — | — | — | — | — | **BLOCKED** — see below |

**Must:** llama-server without `-rea off` → parse_ok 0 (thinking tokens). Documented in `stalls.json`.

### Parallel throughput note

Not measured (vLLM blocked; matrix used `-np 1`). For atg ready-queue: try llama-server `-np` = concurrency after a smoke, or Ollama with multiple runners; validate Choice quality under load before adopting.

## 3) vLLM status

| Item | Status |
|------|--------|
| `~/DEVELOP/.venv` | Nightly **vllm 0.30.1rc1 rocm723** + torch git — **safe to remove** (Mark approved toss) |
| mpi-shim | `~/DEVELOP/.venv/lib/mpi-shim/libmpi_cxx.so.40` present |
| Ubuntu ROCm | **7.1.x** (`rocm 7.1.0`, hiprtc **7.1**, not 7.2) |
| Present | libMIOpen.so.1, librccl.so.1, libhiprtc.so.7 (7.1), hipfft/hiprand/hipsparse/hipsolver, libroctx64 |
| **Missing** | **libhipsparselt**, **librocprofiler-sdk.so.1** |
| Import | Fails: `librocprofiler-sdk.so.1` |
| Mismatch | Wheel expects **ROCm 7.2.3**; system is **7.1.x** |

**Mark options:** (a) install remaining 7.1 packages if they exist + find a **7.1-matching** vLLM/torch wheel into `~/DEVELOP/pfy-mentat/tmp/vllm-venv`; (b) upgrade userspace to full **ROCm 7.2** to match nightly; (c) skip vLLM and use Ollama / llama-server ROCm.

## 4) Recommendation (atg-framework on nimo)

| Role | Target |
|------|--------|
| Runtime (default) | **Ollama** for `qwen3.6:35b` (best decode) |
| Runtime (big MoE / no double-load) | **llama-server ROCm** `--no-mmap -rea off` |
| Coding model | **`qwen3.6:35b`** (fallback **`qwen3-coder:30b`**) |
| Stretch | **`qwen3-coder-next`** via no-mmap only |
| Decision | **CUA-S1-FORMS** |
| Avoid | GLM-Air / gpt-oss for typed Choice; Ollama-default 51GB+ loads |

## 5) #273 nits folded

- Handoff: replace stale “~22 GB hardware edge” with dual table (Ollama-default vs no-mmap).
- `.gitignore`: bench-5 keeps receipt/peak; bench-4 `receipt-*` ignore documented (force-add was #273 evidence).
- Runner RSS: `test_eacces_exe_falls_back_to_argv0_and_recovers_stats`.
- gpt-oss wbc: Entry 092 receipt **wbc=4** (not “-”); weak Choice overall (parse 26/48).
