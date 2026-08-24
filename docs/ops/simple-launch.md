# Simple launch surface (`./pfy`)

**Goal G8 · ADR-0012 (launcher) · ADR-0014 (inference adapters)**  
**Feel:** install once → start inference → pick a harness (Ollama then Hermes/OpenCode style).

Canonical CLI: `./pfy` → `scripts/pfy` (symlink). Levers: setup/onboard, status, start, stage, ship, eval, harness. Grok remains default harness / **monitor**. Local **worker** uses OpenAI-compat (`PFY_INFERENCE` / `PFY_INFERENCE_URL`).

## New machine (happy path)

```bash
git clone https://github.com/themark-net/pfy-mentat.git
cd pfy-mentat
./pfy setup                 # or: ./pfy setup local-only
./pfy status                # ready | partial | stub + live inference backend
./pfy start                 # default harness = grok (monitor)
# optional:
./pfy harness use opencode
./pfy start
./pfy models pull deepseek-coder:6.7b
./pfy stage                 # green checks
./pfy eval                  # catalog self-mod gates
./pfy ship                  # product verify
```

Install Grok CLI once if missing: `curl -fsSL https://x.ai/cli/install.sh | bash` then re-run `./pfy setup`.  
Local inference adapters (do **not** vendor): Ollama https://ollama.com · Shimmy https://github.com/Michael-A-Kuykendall/shimmy · llama-swap https://github.com/mostlygeek/llama-swap (+ llama.cpp llama-server).

```bash
export PFY_INFERENCE=ollama          # default; or shimmy | llama-swap
export PFY_INFERENCE_URL=http://127.0.0.1:11434/v1   # optional override
```

See [openai-compat-worker.md](openai-compat-worker.md).

## Map to old Make levers

| Simple | Make / script |
|--------|----------------|
| `pfy setup` | `make env-init` + `bootstrap/grok-cli/install.sh` |
| `pfy stage` | `make env-stage` |
| `pfy ship` | `make product-ship` |
| `pfy eval` | `make eval-integration-change` |
| Platform deep dives | `make help` (cage, smokes, matrix) |

## Harness status legend

| Live status | Meaning |
|-------------|---------|
| **ready** | Binary found **and** (for inference) API responds; start should work |
| **partial** | Installed or documented path incomplete (e.g. Ollama binary but `/api/tags` and `/v1/models` down) |
| **stub** | Slot reserved; `pfy start` prints setup + issue text (exit 2) |
| **missing** | Not installed |
| **detected-stub** | Binary found but adapter still stub |

**T-0101 / Ollama:** `pfy status` reports ollama **ready** only if `curl` to `:11434/api/tags` **or** `/v1/models` succeeds. `pfy start` waits a few seconds (not unbounded); if still down, prints error and **continues** for cloud harnesses (Grok). Never fake ready.

Registry: [`data/harnesses.json`](../../data/harnesses.json). `inference_default` remains `ollama`.

## Stubs (honest)

Hermes, Claude Code, Codex, Gemini/Antigravity-class, Exo full runtime, Continue — **stubbed**. Patterns may already exist as skills/docs; the **unified installer path** does not. Progress tracked on GitHub under label `harness-adapter`. Missing Shimmy/llama-swap binaries: honest note + issue pointer; exit 2 when starting that adapter.

## Why not Make-only?

Builders keep Make. **New operators** get one verb set so they never need to learn `cage-grok-auth-import` on day one. T-0090 MVP already exists; this does not explode Make surface.

## Tracking

| Work | Issue |
|------|------:|
| Epic G8 | [#53](https://github.com/themark-net/pfy-mentat/issues/53) |
| Ollama | [#54](https://github.com/themark-net/pfy-mentat/issues/54) |
| OpenCode | [#55](https://github.com/themark-net/pfy-mentat/issues/55) |
| Hermes | [#56](https://github.com/themark-net/pfy-mentat/issues/56) |
| Claude Code | [#57](https://github.com/themark-net/pfy-mentat/issues/57) |
| Codex | [#58](https://github.com/themark-net/pfy-mentat/issues/58) |
| Gemini | [#59](https://github.com/themark-net/pfy-mentat/issues/59) |
| Exo | [#60](https://github.com/themark-net/pfy-mentat/issues/60) |
| Continue | [#61](https://github.com/themark-net/pfy-mentat/issues/61) |
| agent-cage lab | [#62](https://github.com/themark-net/pfy-mentat/issues/62) |
| Pluggable inference (T-0110) | ADR-0014 |
