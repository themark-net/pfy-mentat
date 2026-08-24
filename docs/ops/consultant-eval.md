# Consultant evaluation pack

Read this first if you are evaluating **code against documentation**. Docs below match shipped `scripts/pfy`, `data/harnesses.json`, and `scripts/detect-local-runtime.sh` on main. Do not treat catalog rows or queued adapter issues as live product.

## Map (every link is in-repo)

| What | Path |
|------|------|
| Design (why / G1–G8) | [docs/DESIGN.md](../DESIGN.md) |
| Architecture snapshot | [docs/ARCHITECTURE.md](../ARCHITECTURE.md) |
| ADR index (incl. 0014, 0015) | [docs/adr/README.md](../adr/README.md) |
| Simple launch | [docs/ops/simple-launch.md](simple-launch.md) |
| Local inference | [docs/ops/local-runtime.md](local-runtime.md) |
| Product levers | [docs/ops/product-operator-surface.md](product-operator-surface.md) |
| Eval gates | [docs/ops/eval-gates-and-ux-uat.md](eval-gates-and-ux-uat.md) |
| Harness registry | [data/harnesses.json](../../data/harnesses.json) |
| Module maps | [docs/modules/README.md](../modules/README.md) |
| Work queue | [docs/TODO.md](../TODO.md) |

## Operator loop (no tribal knowledge)

```bash
git clone https://github.com/themark-net/pfy-mentat.git
cd pfy-mentat
./pfy setup                 # or: ./pfy setup local-only
./pfy status                # live column is authority, not json "status"
./pfy start                 # inference → env-stage → active harness (default grok)
./pfy up                    # same as start
./pfy models                # inspect-only (tag list is not success)
make eval-structural        # G0, no LLM, no cage required
```

Bare `./pfy start` / `./pfy up` = local inference (if any) + `scripts/env-stage.sh` (honest skip) + attach active harness. `./pfy models` never means the stack is ready. `./pfy eval` is catalog self-mod (`make eval-integration-change`), not the consultant G0 lane.

Public CLI must agree: README Simple path, this file, [simple-launch.md](simple-launch.md), and `scripts/pfy` `usage()`.

## Real vs stub vs catalog-only

| Kind | Meaning |
|------|---------|
| **Live harness** | `./pfy start <id>` execs a binary (grok, opencode, hermes) |
| **Inference adapter** | Detector / `ensure_inference`; `./pfy start <engine>` is not a coding agent |
| **Honest stub** | `STUB harness: <id>` + issue URL, **exit 2**. Binary on PATH is `detected-stub`, still not ready |
| **Catalog-only** | Scored in `TOOLS.md` / slim `data/tools.json` ([ADR-0015](../adr/0015-catalog-json-slim-subset.md)). A catalog row is not an installer |

Live path today: **Grok** (monitor, default) + **OpenCode** (host adapter) + **Hermes** (runtime, if binary on PATH) + **detected inference**. Remaining harness ids are stubs. Do not implement those adapters from this pack.

## Honesty matrix (every `data/harnesses.json` id)

Live status comes from `detect_status` in `scripts/pfy` (and the detector for inference). The json `status` field can lag; trust `./pfy status`.

| Live | Meaning |
|------|---------|
| ready | Binary (or API) is usable for start |
| partial | Binary present, HTTP/API down (inference) |
| stub | Slot reserved; start is STUB exit 2 |
| detected-stub | Binary on PATH but adapter still stub |
| missing | No binary |

Detect order (ADR-0014, first live wins): **FreeToken :1919 → llama-swap :9292 → llama-server :8080 → Ollama :11434**. Shimmy is optional last. Override: `PFY_LOCAL_RUNTIME`, `LOCAL_OPENAI_BASE_URL`.

| id | Role | Live `./pfy status` | `./pfy start <id>` |
|----|------|---------------------|--------------------|
| freetoken | inference | Detector if this engine: ready/partial. Else PATH → partial, else missing | Bring-up then spine: if API not ready, honest stub exit 2. Partial start may launch `ft serve` when `PFY_FT_MODEL` (or `LOCAL_CODER_MODEL` / `FREETOKEN_MODEL`) is set |
| llama-swap | inference | Same (port **:9292**) | If HTTP down: print one-liner, no fake ready. Named start exit 2 unless detector ready |
| llama.cpp | inference | Same as llama-server (port **:8080**) | Same as llama-server |
| ollama | inference | Same (port **:11434**). Registry still says adapter incomplete | If binary and API down: fire-and-forget `ollama serve` + `sleep 1` (health wait is **not** shipped). Named start exit 2 unless API ready. `./pfy models pull <name>` still works |
| shimmy | inference | Optional last; PATH-only is partial | HTTP down: STUB one-liner. Named start exit 2 unless ready |
| grok | harness | **ready** if `grok` on PATH; else **missing**. Attach also needs `grok login` / `XAI_API_KEY` | `exec grok` when authenticated. Missing/unauth: print install/login, **do not abort the env**; try next ready adapter (opencode) |
| opencode | harness | **ready** if `opencode` or `opencode-cli` on PATH; else **missing**. json may still say `partial` | Named start: `exec` binary, `OPENCODE_SKILLS` → `bootstrap/grok-cli/skills`, `OPENAI_BASE_URL` from `LOCAL_OPENAI_BASE_URL` when runtime ready. No binary: STUB + issue #55, exit 2 |
| hermes | harness | **ready** if `hermes` or `hermes-agent` on PATH; else **missing**. json may stay `partial` | Named start: `exec` binary; `OPENAI_BASE_URL` from `LOCAL_OPENAI_BASE_URL` when runtime ready. No binary: STUB + issue #56 + `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`, exit 2. `/hermes-feedback` is process-only |
| claude-code | harness | stub / detected-stub | Always STUB exit 2 + issue #57 |
| codex | harness | stub / detected-stub | Always STUB exit 2 + issue #58 |
| gemini | harness | stub / detected-stub | Always STUB exit 2 + issue #59 |
| exo | harness | stub / detected-stub (`exo.sh` in repo or `~/exo/`) | Always STUB exit 2 + issue #60 |
| continue | harness | stub (no detect bins) | Always STUB exit 2 + issue #61 |
| agent-cage | lab | stub / detected-stub. **Docker present is not ready** | Always STUB exit 2 + issue #62. Lab is `make cage-*`, not `./pfy start` |

## Eval without assuming cage

| Command | Needs cage? | Needs LLM? | What green means |
|---------|-------------|------------|------------------|
| `make eval-structural` | No | No | G0 docs/schema scorers. Consultant default |
| `make eval-golden` | No | Replay fixtures | Deterministic golden lane |
| `make eval-deploy-ready` | Declared smokes | Mixed | G1 — skip if smoke needs lab you do not have; do not fake |
| `./pfy eval` | No (Make target may skip) | Catalog change gates | `eval-integration-change`, not G0 |
| `make cage-*` / in-cage smokes | **Yes** | Varies | Optional lab. Missing Docker is skip, not product-ready |

Do not call a lane green if it skipped. Point of truth: [eval-gates-and-ux-uat.md](eval-gates-and-ux-uat.md). Catalog scoring rubric: [evaluation-framework.md](../evaluation-framework.md).

## Out of scope for this pack

- Shipping remaining harness adapters
- Restoring a 1:1 dump of TOOLS.md into tools.json
- Treating agent-cage as a `./pfy start` harness
