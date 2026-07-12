# Example: LiteLLM → Ollama (+ cloud by profile)

**T-0012** — profile recipes under `config/litellm/` + in-cage local smoke.  
**OQ-0002:** option 2 (LiteLLM + Ollama smoke; full eval harness separate).

## Profiles

| `DEPLOY_PROFILE` | Config | Smoke needs cloud? |
|------------------|--------|--------------------|
| `local-only` | [config/litellm/local-only.yaml](../../config/litellm/local-only.yaml) | No |
| `balanced` | [config/litellm/balanced.yaml](../../config/litellm/balanced.yaml) | No for local aliases; yes for `cloud-*` |
| `max-performance` | [config/litellm/max-performance.yaml](../../config/litellm/max-performance.yaml) | Yes for primary; local is fallback |

Full env table: [config/litellm/README.md](../../config/litellm/README.md).

## What the cage smoke proves

A completion request issued **inside agent-cage** goes:

```text
agent (LiteLLM) → cage proxy (policy allow) → host.docker.internal:11435
  → host gateway → 127.0.0.1:11434 (Ollama) → model
```

Default model: **`deepseek-coder:latest`**. Override with `LITELLM_SMOKE_MODEL`.

This smoke always uses the **local OpenAI-compat path** (no cloud key required), regardless of profile. Profile YAML files document routing aliases for operator/proxy use.

## Host prerequisites

| Requirement | Notes |
|-------------|--------|
| Ollama running | `curl http://127.0.0.1:11434/api/tags` |
| Model present | Prefer existing; respect pull disk budget |
| Docker + agent-cage | `make local-ollama-up` or cage with local-ollama overlay |
| **Host gateway** | `./host-ollama-gateway.sh start` (no sudo) |

## Quick start (from catalog root)

```bash
export PATH="$HOME/.local/bin:$PATH"
export DEPLOY_PROFILE=local-only   # or balanced / max-performance
export LITELLM_SMOKE_MODEL=deepseek-coder:latest
export OLLAMA_API_BASE=http://host.docker.internal:11435   # for cage LiteLLM proxy use

./examples/litellm-ollama/host-ollama-gateway.sh start
make local-ollama-overlay-install
make local-ollama-up
make smoke-litellm-ollama     # exit 0; in-cage only
```

### Using profile configs (host proxy sketch)

```bash
export DEPLOY_PROFILE=balanced
export LITELLM_CONFIG=config/litellm/balanced.yaml
export OLLAMA_API_BASE=http://127.0.0.1:11434
export LITELLM_CLOUD_MODEL=xai/grok-3
# XAI_API_KEY from .env
# litellm --config "$LITELLM_CONFIG"   # if using LiteLLM proxy CLI
```

## Files

| Path | Role |
|------|------|
| `pins.env` | Model, ports, profile pins |
| `host-ollama-gateway.sh` | `0.0.0.0:11435` → `127.0.0.1:11434` |
| `smoke_completion.py` | LiteLLM completion check (local) |
| `run-in-cage.sh` | In-container driver |
| `../../config/litellm/*.yaml` | Profile routers (T-0012) |
| `../../harness/agent-cage/overlays/local-ollama/` | Policy + compose fragment |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Pass |
| 1 | Fail (model, network, litellm, empty completion) |
| 2 | Skipped (reserved) |
