# Local / cloud split (pluggable OpenAI-compat + Grok + OpenCode)

**Status:** Active (ADR-0011, ADR-0014)  
**Profiles:** [deployment-profiles.md](deployment-profiles.md) · ADR-0006  
**Smokes:** `make smoke-litellm-ollama` · `make eval-structural` · `make eval-suite` (needs local model)  
**Worker recipe:** [openai-compat-worker.md](openai-compat-worker.md)

## Intent

| Work class | Prefer | Why |
|------------|--------|-----|
| Hard planning, ambiguous design, high-stakes review | **Grok Build** (subscription) | Quality / **monitor** |
| Bulk edit, simple codegen, format, local eval tasks | **Local OpenAI-compat** via OpenCode or LiteLLM | Cost / latency |
| Structural gates (skills, scorers, JSON) | **No LLM** | `make eval-structural` |
| Flexible multi-provider coding CLI | **OpenCode** | Local + cloud in one client |

Grok remains **primary** for bootstrap and cage lab (**monitor**). OpenCode is **first-class secondary** (**worker**). Inference engines are **pluggable adapters** (Shimmy | llama-swap+llama-server | Ollama). Ollama is not the only spine (T-0101 = adapter completeness).

## Topology

```text
                    +---------------------+
   hard tasks       |  Grok Build CLI     |  <- subscription / xAI  MONITOR
                    |  (+ agent-cage)     |
                    +----------+----------+
                               |
                    +----------v----------+
   process skills   |  SKILL.md packs     |  bootstrap/grok-cli/skills
   (portable)       |  same procedures    |  -> also OpenCode adapter
                    +----------+----------+
                               |
         +---------------------+---------------------+
         v                     v                     v
   OpenCode CLI          LiteLLM router         Host tools
   (WORKER)              config/litellm/*       make smoke-*
         |                     |
         +----------v----------+
                    |
         OpenAI-compat HTTP  (PFY_INFERENCE / PFY_INFERENCE_URL)
                    |
     +--------------+--------------+
     v              v              v
  Shimmy      llama-swap +     Ollama
  :11435      llama-server     :11434
              :8080            (adapter)
```

Do not vendor engines (ADR-0003). Pin + detect binaries only.

## Host quick start (local-only)

```bash
# 1. Pick an adapter (default ollama)
export PFY_INFERENCE=ollama   # or shimmy | llama-swap
# ollama serve   # if not already a service
# ollama pull deepseek-coder:latest

# 2. Gateway so cage can reach localhost Ollama (Ollama path)
cd /path/to/pfy-mentat
./examples/litellm-ollama/host-ollama-gateway.sh start
curl -sS http://127.0.0.1:11434/api/tags | head
# also: curl -sS http://127.0.0.1:11434/v1/models

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
export EVAL_MODEL=qwen2.5:14b
make eval-suite
```

## OpenCode (secondary surface / worker)

See [bootstrap/opencode/README.md](../../bootstrap/opencode/README.md) and [openai-compat-worker.md](openai-compat-worker.md).

Typical pattern:

- Point OpenCode at `OPENAI_BASE_URL` for the selected adapter (`/v1`).
- Optionally add cloud providers for hard tasks (operator keys in env — never git).
- Load the **same** skill directories via OpenCode's skill/config paths (adapter docs).

## Grok (primary surface / monitor)

```bash
# subscription OIDC
grok login
make cage-grok          # skills + auth import + workspace
# or host: grok
```

Use Grok when the exit card's **goal** needs high reasoning quality or cage integration debugging.

## How offload works **today** (read this)

Passing `eval-suite` with `deepseek-coder:6.7b` proves the **lab can drive that model**. It does **not** switch Grok Build's brain to local inference.

| Mechanism | Offloads agent turns to local? |
|-----------|--------------------------------|
| Eval harness / LiteLLM smoke | Yes (test traffic only) |
| OpenCode (or any client) with `OPENAI_BASE_URL` -> adapter | **Yes — this is the worker** |
| Grok CLI session | No (subscription/cloud) — use as **monitor** |
| Dual session: OpenCode implements, Grok reviews DoD | **`make worker-stage`** + two terminals — [worker-monitor.md](worker-monitor.md) (T-0085) |

**Offload recipe (T-0085):**

```bash
make worker-stage    # smoke + worker.env + monitor-brief.md

# Terminal A — worker
set -a; . examples/opencode-ollama/.generated/worker.env; set +a
export OPENAI_BASE_URL="${PFY_INFERENCE_URL:-$OPENAI_BASE_URL}"
opencode

# Terminal B — monitor
grok   # open monitor-brief.md · /worker-monitor · /agent-loops plan
```

Persist worker model: `LOCAL_CODER_MODEL=deepseek-coder:6.7b` in `.env` (or from `make eval-select-models`).

## Routing heuristic (agents)

Before a multi-step loop, set exit card **budget** and **model tier**:

| Signal | Route |
|--------|--------|
| `make eval-structural` / json / skill text | No LLM |
| Single-file fix, known pattern, eval implement task | **Local worker** (`OPENAI_BASE_URL` / OpenCode) |
| Multi-module design, ADR, unclear product, review | **Grok monitor** |
| Worker failed 3x / no-progress | Escalate to Grok |
| `DEPLOY_PROFILE=local-only` | Never auto-call cloud |
| `balanced` | Local worker first; Grok monitor |
| `max-performance` | Grok first; local fallback |

## Hermes / plugins

- **`/hermes-feedback`** = first-party **pattern** skill (memory / auto-skill / curator).  
- Ollama or OpenCode **Hermes plugins** = optional host experiments; **not** required runtime; do not vendor Hermes Agent (same posture as ADR-0010 for extra primaries). Hermes is **not** an inference spine (ADR-0014).

## Related

- ADR-0014 · ADR-0011 · ADR-0002 · ADR-0006 · ADR-0003  
- [openai-compat-worker.md](openai-compat-worker.md)  
- [human-decision-inventory.md](human-decision-inventory.md)  
- [loop-engineering.md](loop-engineering.md)  
