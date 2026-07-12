# Module: harness/agent-cage

**Purpose:** **Primary integration lab** — versioned Docker sandbox (PNNL agent-cage) so catalog tools are proven **inside** isolation (network policy + MCP), not only on the host.

## Operator: how to run

From **catalog repo root**:

```bash
export PATH="$HOME/.local/bin:$PATH"
make cage-doctor
make cage-setup          # CLI + optional pin clone
make cage-init           # once → ~/.agentcage
make cage-up-mcp         # start stack
make cage-status && make cage-test
make cage-shell          # /workspace ← ~/.agentcage/workspace
make cage-down
```

| Path | Role |
|------|------|
| `~/.agentcage` | Runtime project (compose, policies, workspace) |
| `~/.local/share/pfy-mentat/agent-cage` | Optional source pin checkout |
| `harness/agent-cage/PINNED_COMMIT` | Upstream pin |
| `overlays/grok/` | Grok-in-image + OIDC auth mount |
| `overlays/local-ollama/` | Host Ollama allowlist + compose fragment |
| `overlays/write-guard/` | MCP fragment for write-guard (optional enable) |

Package README: [harness/agent-cage/README.md](../../harness/agent-cage/README.md)

## Where variables live

| Variable | Role |
|----------|------|
| `AGENTCAGE_DIR` | Runtime project (default `~/.agentcage`) |
| `POLICY` | Policy file stem under `policies/` |
| `DEPLOY_PROFILE` | Profile for env-check / recipes |
| `OLLAMA_HOST` / `OPENAI_BASE_URL` | Host vs cage URLs — see [REGISTRY](../../bootstrap/env/REGISTRY.md) |
| Cage Grok auth | `make cage-grok-auth-import` → `~/.agentcage/grok-home/auth.json` |

## Agent map

| Concern | Detail |
|---------|--------|
| **Invariants** | Integration smokes for catalog tools run **in-cage** (ADR harness practice); `agentcage up` may ignore extra compose `-f` — Grok/local-ollama targets call compose explicitly |
| **Network** | Agent → mitmproxy whitelist only; host Ollama needs gateway + policy (`coding-agent-local`) |
| **Do not** | Confuse runtime `~/.agentcage` with this git repo; commit secrets into compose |
| **ADR** | ADR-0003 (pins), ADR-0006 (profiles), ADR-0007 (write-guard layer) |
| **Smokes** | [examples-smokes.md](examples-smokes.md) |

## Verify

```bash
make cage-status
make cage-test                 # policy tests (stack up)
make smoke-write-guard         # optional tool smokes
```
