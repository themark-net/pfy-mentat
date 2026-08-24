# OpenAI-compat local worker (ADR-0014)

Point the **local worker** (OpenCode or any OpenAI SDK client) at a pluggable inference adapter. **Grok stays the monitor** (`make worker-stage`). Never commit secrets.

## Env

| Variable | Role |
|----------|------|
| `PFY_INFERENCE` | `ollama` (default) \\ `shimmy` \\ `llama-swap` |
| `PFY_INFERENCE_URL` | OpenAI-compat base URL (overrides adapter default) |
| `OPENAI_BASE_URL` | Same URL for worker clients |
| `OPENAI_API_KEY` | Dummy/local key if the client requires one — **not** in git |

## Examples (no secrets)

```bash
# Shimmy (lightweight OpenAI server; likely X-name candidate)
export PFY_INFERENCE=shimmy
export PFY_INFERENCE_URL=http://127.0.0.1:11435/v1
export OPENAI_BASE_URL=http://127.0.0.1:11435/v1   # shimmy

# llama-swap + llama.cpp llama-server (hot swap / tok/s)
export PFY_INFERENCE=llama-swap
export PFY_INFERENCE_URL=http://127.0.0.1:8080/v1
export OPENAI_BASE_URL=http://127.0.0.1:8080/v1    # llama-swap

# Ollama adapter (T-0101; remains default)
export PFY_INFERENCE=ollama
export PFY_INFERENCE_URL=http://127.0.0.1:11434/v1
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1  # ollama
```

Do **not** vendor Shimmy, llama.cpp, or Ollama into this repo (ADR-0003). Detect binaries; pin upstream commits in catalog notes when adopted.

## Dual session

```bash
make worker-stage    # smoke + worker.env + monitor-brief.md

# Terminal A — worker (OpenAI-compat local)
set -a; . examples/opencode-ollama/.generated/worker.env; set +a
export OPENAI_BASE_URL="${PFY_INFERENCE_URL:-$OPENAI_BASE_URL}"
opencode

# Terminal B — monitor
grok   # open monitor-brief.md · /worker-monitor · /agent-loops plan
```

Health: `./pfy status` reports live inference; Ollama is **ready** only if `/api/tags` or `/v1/models` responds. `./pfy start` retries a few seconds, then reports and continues for cloud harnesses.

## Related

- ADR-0014 · ADR-0011 · [local-cloud-split.md](local-cloud-split.md) · [simple-launch.md](simple-launch.md) · [worker-monitor.md](worker-monitor.md)
