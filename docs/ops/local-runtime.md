# Local inference runtime (pluggable)

**ADR:** [0014](../adr/0014-pluggable-local-inference-spine.md) · **Issue:** [#76](https://github.com/themark-net/pfy-mentat/issues/76)

Owner bar: `./pfy up` then `./pfy models`. Product door is still `./pfy setup && ./pfy status && ./pfy start`.

## Preferred: FreeToken

[FreeToken](https://github.com/FlashML-org/FreeToken) (`uv pip install "freetoken[accel]"`, then `ft serve --model <hf-or-path>`; `./pfy up` uses **`PFY_FT_MODEL`**).
OpenAI + Anthropic APIs on **:1919**. Desktop: [flashml.ai](https://www.flashml.ai/).

## Fallback order

`scripts/detect-local-runtime.sh`:

1. **freetoken** (`ft` / `freetoken`) — :1919
2. **llama-swap** / **llama-server** — GGUF :8080
3. **Ollama** — :11434 adapter
4. **Shimmy** — optional, not preferred

```bash
export PFY_LOCAL_RUNTIME=freetoken
export LOCAL_OPENAI_BASE_URL=http://127.0.0.1:1919/v1
```

Workers (OpenCode, LiteLLM, eval) use `LOCAL_OPENAI_BASE_URL`. Grok stays the monitor.

Missing binaries are `missing` / `partial`, never fake-healthy. Do not vendor engines.
