# Product operator surface (end-user simplicity)

**Status:** Direction / MVP debt  
**Related:** ADR-0011 · [local-cloud-split.md](local-cloud-split.md) · TODO **T-0090**

## Two audiences

| Audience | Goal | OK complexity |
|----------|------|----------------|
| **End user / product team** | Build *their* product with LLM toolsets | **3 levers** |
| **Platform builders (us)** | Catalog, cage, eval, skills, MCP | Many Make targets OK for now |

MVP iteration may expose many targets. **Ship shape** collapses to the product loop below.

## Absolute minimum levers (target)

```text
1. onboard   — attach this stack to a project (process + skills + profile)
2. stage     — bring up local env (Ollama path + optional cage) green
3. ship      — verify + push product code (not platform code)
```

Suggested final names (implementation: T-0090):

| Lever | Make (eventual) | Does |
|-------|-----------------|------|
| onboard | `make project-onboard DIR=…` | project-process scaffold + skill paths + `.env` profile |
| stage | `make env-stage` | gateway + local smoke + `eval-structural` (+ optional cage) |
| ship | `make product-ship` | product tests/smokes + git push **product** remote |

Everything else is **platform development** (`make help` full list) and may stay advanced/docs-only.

## Local bulk vs cloud monitor (target behavior)

```text
Worker (local Ollama coder, e.g. deepseek-coder:6.7b)
  → implements, runs tests, cheap loops
Monitor (Grok subscription / strong cloud)
  → sets DoD/exit card, reviews, escalates when worker stuck
```

**Today (honest):**

| Path | Uses local `deepseek-coder:6.7b`? |
|------|-----------------------------------|
| `make eval-suite` / `eval-auto` | **Yes** (when selected as gate) |
| `make smoke-litellm-ollama` | Yes (smoke model, often `:latest`) |
| Grok Build interactive agent | **No** — Grok cloud/subscription |
| OpenCode pointed at Ollama | **Yes** if configured (T-0080) |
| Dual session worker/monitor | **`make worker-stage`** + `/worker-monitor` (T-0085) — not a single daemon |

## Redeployable workflow (unchanged north star)

1. **Catalog** tools/skills (rubric / lanes)  
2. **Port patterns** into first-party skills + smokes  
3. **Prove** with `eval-structural` + local suite  
4. **Operate** product via minimal levers  
5. **Sync** platform itself with `cage-code-sync` (builders only)

## Makefile complexity budget (T-0090)

| Allowed on product surface | Belongs in platform/docs only |
|----------------------------|-------------------------------|
| onboard / stage / ship | cage-*, smoke-*, eval-*, sync internals |
| `DEPLOY_PROFILE` | 20+ EVAL_* knobs |
| One local model default from `eval-select-models` | Full matrix debugging |

Audit checkpoint: count public Make targets aimed at product users; goal **≤ 5**.

## Related TODOs

- **T-0085** — Worker/monitor split: OpenCode+Ollama worker, Grok monitor recipe  
- **T-0080** — OpenCode host smoke (required for real offload)  
- **T-0090** — Collapse product surface; audit Make levers  
