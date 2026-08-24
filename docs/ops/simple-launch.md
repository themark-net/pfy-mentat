# Simple launch surface (`./pfy`)

**Goal G8 · ADR-0012**  
**Feel:** install once → start inference → product stage → attach active harness (default grok).

## New machine (happy path)

```bash
git clone https://github.com/themark-net/pfy-mentat.git
cd pfy-mentat
./pfy setup                 # or: ./pfy setup local-only
./pfy status                # ready | partial | stub
./pfy start                 # inference → env-stage → active harness (default grok)
./pfy up                    # same operator bring-up as start
# optional:
./pfy harness use opencode
./pfy start                 # uses active harness if live-ready
./pfy start grok            # named harness after inference/stage
./pfy models                # inspect-only (tag list is not success)
./pfy models pull deepseek-coder:6.7b
./pfy stage                 # re-run product stage
./pfy eval                  # catalog self-mod gates
./pfy ship                  # product verify
```

Install Grok CLI once if missing: `curl -fsSL https://x.ai/cli/install.sh | bash` then `grok login` (missing/unauth grok does not abort the env; another ready adapter such as opencode is attached if present).  
Install Ollama for the **adapter** path (not the spine): https://ollama.com
When the detector selects Ollama (or `PFY_LOCAL_RUNTIME=ollama`), `./pfy start` / `./pfy up` wait for real health (`GET /api/tags` or `/v1/models`), then pull/select `PFY_OLLAMA_MODEL` (else `LOCAL_CODER_MODEL`). Honest skip if no name and none installed. Status is **ready** only when the API responds (binary + API down = partial; no binary = missing). `./pfy models pull <name>` still works.

## Map to old Make levers

| Simple | Make / script |
|--------|----------------|
| `pfy setup` | `make env-init` + `bootstrap/grok-cli/install.sh` |
| `pfy start` / `pfy up` | inference + `scripts/env-stage.sh` + active harness |
| `pfy stage` | `make env-stage` |
| `pfy ship` | `make product-ship` |
| `pfy eval` | `make eval-integration-change` |
| Platform deep dives | `make help` (cage, smokes, matrix) |

## Harness status legend

| Live status | Meaning |
|-------------|---------|
| **ready** | Binary found; start should work |
| **partial** | Installed or documented path incomplete |
| **stub** | Slot reserved; `pfy start` prints setup + issue text |
| **missing** | Not installed |
| **detected-stub** | Binary found but adapter still stub |

Registry: [`data/harnesses.json`](../../data/harnesses.json).

## Stubs (honest)

`hermes`, `claude-code`, `codex`, `gemini`, `exo`, `continue`, `agent-cage` stay stubbed. `./pfy start <id>` prints `STUB harness: <id>`, the GitHub issue URL from `data/harnesses.json` when set, and **exits 2**. `./pfy status` / `harness list` show `stub` (or `detected-stub` if a binary is on PATH). A binary or Docker on PATH is **not** ready.

Patterns may already exist as skills/docs; the unified installer path does not. Progress tracked on GitHub under label `harness-adapter`.

## Why not Make-only?

Builders keep Make. **New operators** get one verb set so they never need to learn `cage-grok-auth-import` on day one.

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
