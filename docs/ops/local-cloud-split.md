# Local / cloud split (Ollama + Grok + OpenCode)

**Status:** Active (ADR-0011)  
**Profiles:** [deployment-profiles.md](deployment-profiles.md) · ADR-0006  
**Smokes:** `make smoke-litellm-ollama` · `make eval-structural` · `make eval-suite` (needs Ollama)

## Intent

| Work class | Prefer | Why |
|------------|--------|-----|
| Hard planning, ambiguous design, high-stakes review | **Grok Build** (subscription) | Quality |
| Bulk edit, simple codegen, format, local eval tasks | **Ollama** via OpenCode or LiteLLM | Cost / latency |
| Structural gates (skills, scorers, JSON) | **No LLM** | `make eval-structural` |
| Flexible multi-provider coding CLI | **OpenCode** | Local + cloud in one client |

Grok remains **primary** for bootstrap and cage lab. OpenCode is **first-class secondary** for cost-aware routing.

## Topology

```text
                    ┌─────────────────────┐
   hard tasks       │  Grok Build CLI     │ ← subscription / xAI
                    │  (+ agent-cage)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
   process skills   │  SKILL.md packs     │  bootstrap/grok-cli/skills
   (portable)       │  same procedures    │  → also OpenCode adapter
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
   OpenCode CLI          LiteLLM router         Host tools
   (local/cloud)         config/litellm/*       make smoke-*
         │                     │
         └──────────► Ollama (host :11434)
                      gateway :11435 for cage
```

## Host quick start (local-only)

```bash
# 1. Ollama on host
ollama serve   # if not already a service
ollama pull deepseek-coder:latest   # or qwen2.5:14b for eval gate

# 2. Gateway so cage can reach localhost Ollama
cd /path/to/pfy-mentat
./examples/litellm-ollama/host-ollama-gateway.sh start
curl -sS http://127.0.0.1:11434/api/tags | head

# 3. Profile
export DEPLOY_PROFILE=local-only
make env-check   # or env-init first

# 4. Prove path
make local-ollama-overlay-install
make local-ollama-up
make smoke-litellm-ollama     # in-cage completion

# 5. Structural always
make eval-structural

# 6. Model eval when gate model present
export EVAL_MODEL=qwen2.5:14b   # or smaller for smoke
make eval-suite                 # or SKIP if model missing
```

## OpenCode (secondary surface)

See [bootstrap/opencode/README.md](../../bootstrap/opencode/README.md).

Typical pattern:

- Point OpenCode at `http://127.0.0.1:11434/v1` (Ollama OpenAI compat) for local models.
- Optionally add cloud providers for hard tasks (operator keys in env — never git).
- Load the **same** skill directories via OpenCode’s skill/config paths (adapter docs).

## Grok (primary surface)

```bash
# subscription OIDC
grok login
make cage-grok          # skills + auth import + workspace
# or host: grok
```

Use Grok when the exit card’s **goal** needs high reasoning quality or cage integration debugging.

## How offload works **today** (read this)

Passing `eval-suite` with `deepseek-coder:6.7b` proves the **lab can drive that model**. It does **not** switch Grok Build’s brain to Ollama.

| Mechanism | Offloads agent turns to local? |
|-----------|--------------------------------|
| Eval harness / LiteLLM smoke | Yes (test traffic only) |
| OpenCode (or any client) with `OPENAI_BASE_URL` → Ollama | **Yes — this is the worker** |
| Grok CLI session | No (subscription/cloud) — use as **monitor** |
| Dual session: OpenCode implements, Grok reviews DoD | **Manual today** → automate in T-0085 |

**Practical offload recipe (until T-0085):**

```bash
# Terminal A — local worker
export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
export OPENAI_API_KEY=ollama
# OpenCode (or compatible) model = deepseek-coder:6.7b  # from make eval-select-models
# Load skills from bootstrap/grok-cli/skills

# Terminal B — cloud monitor
grok   # or make cage-grok-shell → grok
# /agent-loops plan + /one-shot DoD; review worker diffs; escalate only when stuck
```

Persist the selected worker model:

```bash
make eval-select-models
# copy EVAL_MODEL=… into .env as LOCAL_CODER_MODEL=
```

## Routing heuristic (agents)

Before a multi-step loop, set exit card **budget** and **model tier**:

| Signal | Route |
|--------|--------|
| `make eval-structural` / json / skill text | No LLM |
| Single-file fix, known pattern, eval implement task | **Local worker** (`LOCAL_CODER_MODEL` / OpenCode→Ollama) |
| Multi-module design, ADR, unclear product, review | **Grok monitor** |
| Worker failed 3× / no-progress | Escalate to Grok |
| `DEPLOY_PROFILE=local-only` | Never auto-call cloud |
| `balanced` | Local worker first; Grok monitor |
| `max-performance` | Grok first; local fallback |

## Hermes / plugins

- **`/hermes-feedback`** = first-party **pattern** skill (memory / auto-skill / curator).  
- Ollama or OpenCode **Hermes plugins** = optional host experiments; **not** required runtime; do not vendor Hermes Agent (same posture as ADR-0010 for extra primaries).

## Related

- ADR-0011 · ADR-0002 · ADR-0006  
- [human-decision-inventory.md](human-decision-inventory.md)  
- [loop-engineering.md](loop-engineering.md)  
