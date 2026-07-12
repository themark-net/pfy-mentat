# Example: LiteLLM → Ollama (local-only), smoked inside agent-cage

**TODO:** T-0012 (recipe) + T-0021 (in-cage smoke MVP)  
**OQ-0002:** option 2 (LiteLLM + Ollama smoke; no full eval harness)

## What this proves

A completion request issued **inside agent-cage** goes:

```text
agent (LiteLLM) → cage proxy (policy allow) → host.docker.internal:11435
  → host gateway → 127.0.0.1:11434 (Ollama) → model
```

Default model: **`deepseek-coder:latest`** (smallest coding model already present on the operator host when this was written, ~0.8 GB). Override with `LITELLM_SMOKE_MODEL`.

## Host prerequisites

| Requirement | Notes |
|-------------|--------|
| Ollama running | `curl http://127.0.0.1:11434/api/tags` |
| Model present or pull budget | Prefer existing; max pull disk **150 GB** (operator policy) |
| Docker + agent-cage | `make cage-up-mcp` path; smoke uses local overlay |
| **Host gateway** | Ollama is often **localhost-only**; run `./host-ollama-gateway.sh start` (no sudo) |

### Optional: rebind Ollama (sudo)

If you prefer not to use the gateway, bind Ollama publicly on the host (firewall carefully):

```bash
# example — requires sudo; not done by this recipe by default
sudo systemctl edit ollama
# [Service]
# Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Then point cage URLs at `host.docker.internal:11434` instead of `11435`.

## Quick start (from catalog root)

```bash
export PATH="$HOME/.local/bin:$PATH"
export DEPLOY_PROFILE=local-only
export LITELLM_SMOKE_MODEL=deepseek-coder:latest   # or another local coding tag

./examples/litellm-ollama/host-ollama-gateway.sh start
make local-ollama-overlay-install
make local-ollama-up          # policy coding-agent-local + compose fragment
make smoke-litellm-ollama     # MUST exit 0; runs only via agent-cage
```

## Files

| Path | Role |
|------|------|
| `pins.env` | Model, ports, profile pins |
| `host-ollama-gateway.sh` | `0.0.0.0:11435` → `127.0.0.1:11434` |
| `smoke_completion.py` | LiteLLM completion check |
| `run-in-cage.sh` | In-container driver (pip + smoke) |
| `config/litellm/local-only.yaml` | Router sketch for local-only profile |
| `../../harness/agent-cage/overlays/local-ollama/` | Policy + compose fragment |

## Env vars (REGISTRY)

| Variable | On host | Inside cage |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | `http://host.docker.internal:11435` |
| `OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` | `http://host.docker.internal:11435/v1` |
| `LITELLM_SMOKE_MODEL` | e.g. `deepseek-coder:latest` | same |
| `DEPLOY_PROFILE` | `local-only` for this MVP | same |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Pass |
| 1 | Fail (model, network, litellm, empty completion) |
| 2 | Skipped (not used in MVP) |
