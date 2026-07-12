# Environment variable registry

**Purpose:** Single inventory of variables used by this catalog stack.  
**Secrets never go in git.** Only names, purpose, profile affinity, and provisioning rules live here.

When integrating a new tool, **add a row here in the same PR** as the integration.

## Provisioning rules

| Rule | Practice |
|------|----------|
| Init | `make env-init` copies `.env.example` → `.env` (gitignored) if missing |
| Secrets | Operator fills `.env` or exports vars; never commit `.env` |
| Cage | Non-secret vars may be passed into agent-cage via compose env / policy; secrets only via runtime env, not image layers |
| Profiles | `DEPLOY_PROFILE=local-only\|balanced\|max-performance` selects which backends are required vs optional |
| Divergence | Profile-specific overrides in `config/profiles/<name>.env` (no secrets) + optional `.env.local` (gitignored) |

## Registry

| Variable | Secret? | Required profiles | Default / example | Used by | Notes |
|----------|---------|-------------------|-------------------|---------|-------|
| `DEPLOY_PROFILE` | no | all | `balanced` | bootstrap, harness, recipes | Selects local-only / balanced / max-performance |
| `AGENTCAGE_DIR` | no | harness | `$HOME/.agentcage` | harness/agent-cage, agentcage CLI | Runtime cage project after `init` |
| `PATH` (incl. `~/.local/bin`) | no | all | — | grok, agentcage, uv tools | Document in README only |
| `XAI_API_KEY` | **yes** | optional / CI | — | Grok **API key fallback** only | Used if **no** session in `auth.json`. Subscription users usually **do not** need this |
| Host `~/.grok/auth.json` | **yes** | Grok Build default | created by `grok login` | Grok CLI OIDC/browser session | **Primary auth** for interactive Grok; mode `oidc` + refresh_token |
| Cage `~/.agentcage/grok-home/auth.json` | **yes** | grok-in-cage | via `make cage-grok-auth-import` | Grok inside agent container | Copy of host session or device-login result; chmod 600 |
| `GROK_HOME` | no | optional | `$HOME/.grok` | Grok CLI state dir | In cage: `/home/agent/.grok` (volume) |
| `POLICY` | no | harness | `default`, `coding-agent-grok`, or `coding-agent-local` | agent-cage compose | `coding-agent-local` allows `host.docker.internal` for host Ollama |
| `OPENAI_API_KEY` | **yes** | optional | — | LiteLLM OpenAI backends | Optional cloud fallback |
| `ANTHROPIC_API_KEY` | **yes** | optional | — | Claude-in-cage experiments | Optional |
| `OPENAI_BASE_URL` | no | local-only, balanced | Host: `http://127.0.0.1:11434/v1` · **Cage:** `http://host.docker.internal:11435/v1` | LiteLLM, agents → Ollama | Inside cage use **gateway port 11435** (user-space forward to host Ollama). Stock Ollama often binds 127.0.0.1 only |
| `OLLAMA_HOST` | no | local-only, balanced | Host: `http://127.0.0.1:11434` · **Cage:** `http://host.docker.internal:11435` | Ollama clients | Same gateway split as `OPENAI_BASE_URL` |
| `OLLAMA_GATEWAY_PORT` | no | local-only, balanced (cage smokes) | `11435` | `examples/litellm-ollama/host-ollama-gateway.sh` | Publishes `0.0.0.0:11435` → `127.0.0.1:11434` without sudo |
| `LITELLM_SMOKE_MODEL` | no | smoke | `deepseek-coder:latest` | `make smoke-litellm-ollama` | Prefer smallest local coding model already pulled |
| `LITELLM_MASTER_KEY` | **yes** | optional | — | LiteLLM proxy auth | If running shared LiteLLM |
| `LITELLM_CONFIG` | no | optional | `config/litellm/local-only.yaml` | LiteLLM | Router sketch for local-only; see `examples/litellm-ollama/` |
| `GROK_HOME` | no | all | `$HOME/.grok` | Grok CLI | Skills, config, sessions |
| `CODEBASE_MEMORY_MCP` | no | optional | `codebase-memory-mcp` | Grok MCP | Command on PATH |
| `WRITE_GUARD_MODE` | no | all (when MCP enabled) | `audit` | write-guard MCP (planned) | `off` \| `audit` \| `enforce` |
| `WRITE_GUARD_ROOTS` | no | cage | `/workspace` | write-guard MCP | Allowed write roots |
| `HF_TOKEN` | **yes** | optional | — | colibri/HF weights | Only if OQ-0008 allows downloads |
| `GITHUB_TOKEN` | **yes** | optional | — | gh, private clones | Prefer fine-scoped PAT |

## Profile affinity

| Profile | Must have | Optional | Must not require |
|---------|-----------|----------|------------------|
| `local-only` | Ollama (or other local OpenAI-compatible) | write-guard, codebase-memory | Cloud API keys for core path |
| `balanced` | Local backend + at least one cloud key (e.g. XAI) | LiteLLM, cage MCP | — |
| `max-performance` | Cloud keys (XAI and/or others) | Local as fallback | Blocking on local GPU |

See [config/profiles/](../../config/profiles/) and [docs/ops/deployment-profiles.md](../../docs/ops/deployment-profiles.md).
