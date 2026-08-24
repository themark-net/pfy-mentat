## Pluggable local inference (v0.4.14 · ADR-0014)

Stage 0 conceptual scores. Do **not** vendor engines. Worker talks OpenAI-compat (`PFY_INFERENCE` / `PFY_INFERENCE_URL`). Grok remains monitor. See [openai-compat-worker.md](openai-compat-worker.md). Matching rows also belong in `TOOLS.md` Active Catalog (Shimmy, llama-swap, llama.cpp llama-server).

| Tool | Primary Cat | GitHub | S1 | S2 | S3 | S4 | Overall | Tier | Key Tags | Integration Notes |
|------|-------------|--------|----|----|----|----|---------|------|----------|-------------------|
| **Shimmy** | Inference & Serving | https://github.com/Michael-A-Kuykendall/shimmy | 92 | 78 | 88 | 75 | 84 | A | #local-first #openai-compat #gguf #rust #inference | X-name lightweight OpenAI server; adapter `data/harnesses.json` id=shimmy; default `http://127.0.0.1:11435/v1`; I1; do not vendor. No x_post_id until a real post is logged. |
| **llama-swap** | Proxy & Routing | https://github.com/mostlygeek/llama-swap | 88 | 72 | 90 | 80 | 83 | A | #local-first #openai-compat #llama.cpp #model-swap #inference | Proxy in front of llama-server for hot swap / tok/s; adapter id=llama-swap; default `http://127.0.0.1:8080/v1`; I1; do not vendor. |
| **llama.cpp llama-server** | Inference & Serving | https://github.com/ggml-org/llama.cpp | 85 | 95 | 80 | 85 | 88 | A | #local-first #openai-compat #gguf #high-perf #quantized | Engine behind llama-swap. TOOLS.md already lists **llama.cpp** (server mode). Do not vendor. I1. |
