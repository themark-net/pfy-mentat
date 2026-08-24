# Local inference runtime (pluggable)

**ADR:** [0014](../adr/0014-pluggable-local-inference-spine.md) · **Issue:** [#76](https://github.com/themark-net/pfy-mentat/issues/76)

Product door is still `./pfy setup && ./pfy status && ./pfy start` (onboard / stage / ship). This page is how the **local worker** gets a model.

## Pick order

`scripts/detect-local-runtime.sh` (used by `./pfy status` / `start`):

1. **llama-swap** (fronts llama-server) — tok/s + hot-swap
2. **llama-server** — one model, raw llama.cpp
3. **Shimmy** — tiny Rust OpenAI-compat; “free forever”; candidate, not required
4. **Ollama** — first-class adapter (T-0101), never removed

Override:

```bash
export PFY_LOCAL_RUNTIME=shimmy          # or llama-swap | llama-server | ollama
export LOCAL_OPENAI_BASE_URL=http://127.0.0.1:11435/v1
```

Workers (OpenCode, LiteLLM, eval) should use `LOCAL_OPENAI_BASE_URL`. Grok stays the monitor.

## Honest stubs

If a binary is on PATH but not serving, `./pfy start` says **STUB/partial** and points at #76. Missing is `missing`, not a fake healthy status.

Do not vendor llama.cpp / Shimmy / llama-swap into this repo.
