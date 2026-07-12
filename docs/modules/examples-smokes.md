# Module: examples/ + pipelines/smoke/

**Purpose:** **Idempotent in-cage integration smokes** for catalog tools. Host checks alone do not prove isolation.

## Operator: how to run

Cage agent must be running (`make cage-up-mcp` or `make local-ollama-up`).

| Target | What it proves |
|--------|----------------|
| `make smoke-write-guard` | write-guard policy audit/enforce |
| `make smoke-codebase-memory` | codebase-memory-mcp index + search |
| `make smoke-repowise` | repowise health (zero LLM) |
| `make smoke-context-tools` | both context tools + compare note |
| `make smoke-litellm-ollama` | LiteLLM → host Ollama via gateway :11435 |

| Layout | Role |
|--------|------|
| `examples/<tool>/` | README, pins.env, run-in-cage.sh, fixtures |
| `pipelines/smoke/<tool>/` | Short pointer + results.latest.md |
| `pipelines/smoke/context-tools-compare.md` | T-0013 complement note |

One-shot paste DoDs: [docs/ops/one-shot-example-dods.md](../ops/one-shot-example-dods.md)

## Where variables live

| Variable | Smoke |
|----------|--------|
| `LITELLM_SMOKE_MODEL` | litellm-ollama (default `deepseek-coder:latest`) |
| `REPOWISE_PIP_SPEC` | repowise (default `repowise==0.30.0`) |
| `OLLAMA_GATEWAY_PORT` | host gateway (default `11435`) |
| `WRITE_GUARD_*` | write-guard |

## Agent map

| Concern | Detail |
|---------|--------|
| **Invariants** | Exit 0 pass, 1 fail; prefer cage; pin deps (ADR-0003) |
| **Do not** | Claim integration green from host-only pip install |
| **Framework** | [harness-integration-framework.md](../ops/harness-integration-framework.md) |

## Verify

```bash
make smoke-write-guard
make smoke-context-tools
# optional if Ollama up:
./examples/litellm-ollama/host-ollama-gateway.sh start && make smoke-litellm-ollama
```
