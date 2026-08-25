# Simple launch surface (`./pfy`)

**Goal G8 · ADR-0012**  
**Feel:** install once → start inference → product stage → attach active harness (default grok).

Consultant map (real vs stub vs catalog): [consultant-eval.md](consultant-eval.md).

## New machine (happy path)

```bash
git clone https://github.com/themark-net/pfy-mentat.git
cd pfy-mentat
./pfy setup                 # or: ./pfy setup local-only
./pfy status                # live column is authority (ready | partial | stub | detected-stub | missing)
./pfy board                 # local operator GUI; chips == status live column
./pfy start                 # inference → env-stage → active harness (default grok)
./pfy up                    # same operator bring-up as start
# optional:
./pfy harness use opencode
./pfy start                 # uses active harness if live-ready
./pfy start grok            # named harness after inference/stage
./pfy models                # inspect-only (tag list is not success)
./pfy models pull deepseek-coder:6.7b
./pfy stage                 # re-run product stage
./pfy stage --lab           # optional personal cage lab (doctor → setup → up-mcp)
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
| `pfy board` | local GUI on 127.0.0.1 — polls detector JSON + `./pfy status` stdout + process table (no pfy daemon) |
| `pfy stage` | `make env-stage` |
| `pfy stage --lab` | `make cage-doctor` then `cage-setup` then `cage-up-mcp` (missing Docker: honest skip) |
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
| **detected-stub** | Binary found but adapter still stub (`agent-cage` + Docker on PATH). Continue is **never** detected-stub. |
| **skip** | Honest skip (a stage piece missing); not a fake ready |

Board chips on `./pfy board` **must equal** this live column. Ignore json `status`.

Registry: [`data/harnesses.json`](../../data/harnesses.json).

## Stubs (honest)

`agent-cage` stays stubbed for start (`./pfy start agent-cage` is STUB + issue #62, exit 2, copy `pfy harness use grok`). Docker on PATH is **detected-stub**, still not startable. Active `agent-cage`: bare `./pfy start` is also STUB exit 2 with **no** grok/opencode fallback. Optional personal lab: `./pfy stage --lab` maps to `make cage-doctor`, `cage-setup`, `cage-up-mcp`. Missing Docker is honest skip, not product-ready. Do not sell cage.

`exo` is an **optional lab** adapter when `exo.sh` is at `$ROOT/exo.sh`, `$HOME/exo/exo.sh`, or on PATH (`./pfy start exo` execs it; missing: STUB + issue #60 + official setup.sh one-liner, exit 2). Not the default harness. Not a Grok replacement. `./pfy harness use exo` does not change `default_harness` (stays grok). Do not vendor Exo. Personal lab-IT only.

Continue is a **config recipe** at `bootstrap/continue/` (`LOCAL_OPENAI_BASE_URL`, not Ollama-only). Live status is always **stub** (never detected-stub). `./pfy start continue` stays STUB exit 2. Active continue: bare `./pfy start` is STUB exit 2, no fallback; copy `pfy harness use grok`.

`gemini` is a live adapter when `gemini` or `gemini-cli` is on PATH (`./pfy start gemini` execs it; missing: STUB + issue #59 + official install one-liner, exit 2). Login/credentials/2FA are owner-only.

`codex` is a live adapter when `codex` is on PATH (`./pfy start codex` execs it; missing: STUB + issue #58 + official install one-liner, exit 2). Login/credentials/2FA are owner-only.

`claude-code` is a live adapter when `claude` is on PATH (`./pfy start claude-code` execs it; missing: STUB + issue #57 + official install one-liner, exit 2). Login/credentials/2FA are owner-only. Optional skills-external path is documentation only.

`hermes` is a live adapter when `hermes` or `hermes-agent` is on PATH (`./pfy start hermes` execs it; missing: STUB + issue #56 + install one-liner, exit 2). `/hermes-feedback` stays process-only. `./pfy start <id>` prints `STUB harness: <id>`, the GitHub issue URL from `data/harnesses.json` when set, and **exits 2**. `./pfy status` / `harness list` show `stub` (or `detected-stub` if a binary is on PATH). A binary or Docker on PATH is **not** ready.

Patterns may already exist as skills/docs; the unified installer path does not. Progress tracked on GitHub under label `harness-adapter`.

## Operator board

`./pfy board` serves a **local** GUI on `127.0.0.1` (default `:3847`, override `PFY_BOARD_PORT`). It is an independent poller of detector JSON, `./pfy status` stdout, and the process table. There is **no pfy daemon**. The board is not a supervisor; `./pfy start` still execs the harness.

Honesty chips for every `data/harnesses.json` id match the live STATUS column. Consultants: eval board chips vs `./pfy status` on an Ollama-only host and on a host with no harness binary. nimo is an Actions runner with Ollama `:11434`, not a pfy profile. Empty `ollama ps` is OK. Grok chip is PATH-only (auth is attach-time; no invented auth column). `DEPLOY_PROFILE=local-only` never auto-calls cloud.

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
