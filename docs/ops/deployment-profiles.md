# Deployment profiles

**Status:** Design accepted in spirit; implementation incremental  
**Related:** [bootstrap/env/REGISTRY.md](../../bootstrap/env/REGISTRY.md), ADR-0006 (profiles), ADR-0007 (write-guard)

## Why

Integrations need a **knob**, not a single hard-coded stack:

| Gradient | Intent |
|----------|--------|
| **local-only** | Airgap-friendly / cost-control / privacy: no cloud required for core agent loops |
| **balanced** | Default: local models for bulk (edit, grep-class, simple gen); cloud (e.g. Grok) for hard planning/reasoning |
| **max-performance** | Quality/latency first: cloud primary; local optional fallback |

Anything between is a **custom profile** (copy `balanced.env` → `config/profiles/custom.env` + `.env` secrets).

## How selection works

```text
DEPLOY_PROFILE=balanced
        │
        ▼
config/profiles/balanced.env   (non-secret defaults)
        │
        ▼
.env / environment             (secrets + operator overrides)
        │
        ▼
tools (Grok, LiteLLM, cage, Ollama, …)
```

Init:

```bash
make env-init                 # .env from example if missing
# edit .env: set DEPLOY_PROFILE and secrets
make env-check                # validate required vars for profile
```

## Routing sketch (LiteLLM later)

| Profile | Default completion | Fallback |
|---------|-------------------|----------|
| local-only | `ollama/*` | fail closed if local down |
| balanced | local for “small” tasks; `xai/*` or grok for “large” | operator-defined |
| max-performance | `xai/*` / strong cloud | local if cloud rate-limited |

Exact model IDs live in `config/litellm/` when that recipe lands (T-0012) — not hard-coded here.

## Cage interaction

- **local-only:** cage still useful for isolation; allowlist should include local registries/Ollama host gateway as needed.
- **balanced / max-performance:** cage proxy must allow required cloud API hosts (document per tool in REGISTRY + policy notes).
- Secrets: inject at **runtime** into host processes or cage env files that are **not** committed and **not** baked into images.

## Gradient extensions (future)

- `balanced-cpu` / `balanced-gpu`
- `max-performance-eu` (region-constrained endpoints)
- Cost caps: max cloud tokens/day via LiteLLM budgets

Record new named profiles under `config/profiles/` and a row in REGISTRY when promoted.
