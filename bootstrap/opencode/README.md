# OpenCode adapter (secondary operator surface)

**Policy:** [ADR-0011](../../docs/adr/0011-hybrid-operator-surfaces-grok-opencode-ollama.md)  
**Primary remains:** Grok (`bootstrap/grok-cli/`)  
**Goal:** Same process skills and local Ollama path without forking doctrine.

## Why this package exists

OpenCode is flexible for **local + cloud** model splits. Our Grok customizations that matter for **design/coding quality** are mostly:

1. **SKILL.md procedures** (portable markdown)  
2. **Process layout** (DESIGN/ADR/TODO/OQ)  
3. **Lab smokes** (agent-cage + LiteLLM→Ollama)  

They should not be Grok-only forever. This package documents the **thin adapter** — not a second skill monorepo.

## Skill portability map

| First-party skill (SoT) | Portable? | OpenCode note |
|-------------------------|-----------|---------------|
| `adr`, `docs`, `open-questions`, `project-process` | Yes | Point OpenCode skills path at `bootstrap/grok-cli/skills/<name>` or copy into OpenCode skill dir |
| `one-shot`, `agent-loops`, `investigate`, `hermes-feedback` | Yes | Same; references to `make …` stay valid from repo root |
| `catalog-docs` | Yes (this repo) | Project-specific |
| `marketing-council` | Yes | Large; optional |
| Grok `install.sh` / `~/.grok/config.toml` | **No** | Grok-only; OpenCode uses its own config |
| Cage `make cage-grok` image | **No** | Grok-in-image; OpenCode-in-cage is later (T-0080) |
| mattpocock / ponytail via `skills.paths` | Yes | Same directories under `skills-external/` |

**Source of truth for skill text:** `bootstrap/grok-cli/skills/` (and sibling `project-process`).  
**Do not** maintain a divergent copy under `bootstrap/opencode/skills/` unless a CLI-specific glue file is required (prefer a 10-line README pointer).

## Suggested host layout

```bash
# Example — adjust to OpenCode’s current skill discovery docs
export OPENCODE_SKILLS="$PWD/bootstrap/grok-cli/skills"
# or symlink individual skills into OpenCode’s user skill directory
```

Configure OpenCode model provider:

| Use | Endpoint / model |
|-----|------------------|
| Local bulk | Ollama OpenAI-compat `http://127.0.0.1:11434/v1` · e.g. `deepseek-coder`, `qwen2.5-coder` |
| Hard tasks | Cloud provider keys in env **or** keep hard tasks on Grok CLI |
| Router | Optional LiteLLM proxy with `config/litellm/balanced.yaml` |

## Shared commands (CLI-agnostic)

```bash
make eval-structural          # always
make smoke-litellm-ollama     # local path proof (cage)
make env-check                # DEPLOY_PROFILE
```

## Non-goals

- Replacing Grok cage auth/OIDC with OpenCode  
- Vendoring OpenCode or Hermes upstream into git  
- Full parity of Grok TUI features inside OpenCode  

## Smoke (T-0080)

```bash
export LOCAL_CODER_MODEL=deepseek-coder:6.7b
make smoke-opencode-ollama
# details: examples/opencode-ollama/README.md
```

## Next implementation slices

| ID | Item |
|----|------|
| T-0080 | ~~Host OpenCode + Ollama smoke~~ **done** (`make smoke-opencode-ollama`) |
| T-0085 | Worker/monitor dual-session automation |
| T-0081 | Optional OpenCode-in-cage smoke |
| T-0074 | `eval-auto` / suite on selected gate |

## Related

- [docs/ops/local-cloud-split.md](../../docs/ops/local-cloud-split.md)  
- [examples/litellm-ollama/](../../examples/litellm-ollama/)  
