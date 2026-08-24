# ADR-0014: Pluggable local inference spine

**Status:** Accepted  
**Date:** 2026-08-24  
**Deciders:** CEO (org), implement on `feat/local-runtime-spine`  
**Issue:** [#76](https://github.com/themark-net/pfy-mentat/issues/76)

## Context

ADR-0011 made **Ollama** the local worker spine (OpenCode / LiteLLM / `LOCAL_CODER_MODEL`) with Grok as monitor. G8 / ADR-0012 still wants `./pfy setup|status|start` to feel like “inference up once, harnesses attach.”

By 2026 that Ollama-only assumption is stale:

- Operators migrate to **llama.cpp `llama-server`** plus **[llama-swap](https://github.com/mostlygeek/llama-swap)** for hot-swap, TTL unload, and better tok/s than the Ollama wrapper.
- **[Shimmy](https://github.com/Michael-A-Kuykendall/shimmy)** is the X-hyped tiny Rust OpenAI-compat server (“FREE forever”) that auto-discovers Ollama/HF/LM Studio GGUF.
- pfy-mentat still hard-codes `ollama serve` and `:11434` in `./pfy start`.

We need **equivalent orchestration, local-first**, without vendoring engines (ADR-0003) or a new product CLI (T-0090).

## Decision

Local inference is a **pluggable OpenAI-compatible endpoint**, not a vendor.

**Detect order** (first healthy wins, override with `PFY_LOCAL_RUNTIME` / `LOCAL_OPENAI_BASE_URL`):

1. **llama-swap** (or a live `llama-server`) — preferred tok/s + multi-model swap
2. **Shimmy** — candidate drop-in; keep if detected, do not require it
3. **Ollama** — first-class adapter (T-0101), never deleted

Workers (OpenCode, LiteLLM, eval, voice) talk to **one** `LOCAL_OPENAI_BASE_URL`. Grok remains monitor / hard tasks (ADR-0002, ADR-0011).

`./pfy status` reports each runtime as `ready | partial | stub | missing`. Missing is honest, not fake-healthy.

## Consequences

- `data/harnesses.json` grows inference rows: `llama-swap`, `llama-server`, `shimmy`, plus existing `ollama`.
- `scripts/detect-local-runtime.sh` is the probe; `./pfy start` uses it instead of Ollama-only.
- Catalog still scores tools; the **product** is onboard / stage / ship + `./pfy`.
- Do not embed llama.cpp, Shimmy, or llama-swap source (pins + detect only).

## Rejected alternatives

| Option | Why not |
|--------|--------|
| Ollama-only | Blocks the 2026 performance path; wrapper overhead vs llama.cpp. |
| Shimmy-only | Young; Airframe/WGSL not proven vs llama.cpp on this hardware. |
| llama.cpp-direct-only | No hot-swap / TTL; llama-swap exists for that. |
| Lychee as default | Tiny project; extends Ollama rather than replacing it. |
| vLLM as default | Cluster/GPU serving, not laptop-first. |
| Vendor any engine into this repo | ADR-0003 / DESIGN non-goals. |
