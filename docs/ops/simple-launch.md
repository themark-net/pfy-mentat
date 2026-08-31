# Simple launch surface (`./pfy`)

**Goal G8 · ADR-0012**  
**Feel:** install once → start inference → product stage → **native operator window**. Attach grok/opencode in-window as a sidecar.

Consultant map (real vs stub vs catalog): [consultant-eval.md](consultant-eval.md).

## New machine (happy path)

```bash
git clone https://github.com/themark-net/pfy-mentat.git
cd pfy-mentat
./pfy setup                 # or: ./pfy setup local-only
./pfy status                # ready | partial | stub
./pfy                       # inference → env-stage → native operator window (no harness exec)
./pfy board                 # same native window; chips == live status column
./pfy start grok            # named harness after inference/stage
./pfy up                    # same as bare ./pfy
# optional:
./pfy harness use opencode
./pfy                      # native window; attach grok/opencode in-window
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
When the detector selects Ollama (or `PFY_LOCAL_RUNTIME=ollama`), `./pfy start` / `./pfy up` wait for real health (`GET /api/tags` or `/v1/models`), then pull/select `PFY_OLLAMA_MODEL` (else `LOCAL_CODER_MODEL`). Honest skip if no name and none installed. Status is **ready** only when the API responds (binary + API down = partial; no binary = missing). `./pfy models pull <name>` still `ollama pull` when Ollama is the live engine.

`./pfy models pull <name>` routes to the live engine. FreeToken (or `ft`/`freetoken` on PATH with no live engine): record the name under `$PFY_STATE_DIR`; next `./pfy` / `./pfy up` uses it for `ft serve --model` (load at serve; no `ft pull`). llama-swap / llama-server: honest skip, no GGUF download. Missing both: honest skip + one-liner, no crash.

When the detector selects FreeToken (or `PFY_LOCAL_RUNTIME=freetoken`), `./pfy start` / `./pfy up` start `ft serve --model $model` in the background if `:1919` is not already healthy, then wait for `GET /v1/models` or `/health`. Model env: `PFY_FT_MODEL`, then `LOCAL_CODER_MODEL`, then `FREETOKEN_MODEL`. Missing binary or no model env is an honest skip (one-liner `ft serve --model $PFY_FT_MODEL`), not fake ready. Still down after wait = partial. Do not vendor FreeToken or invent `ft` flags.

When the detector selects llama-swap (or `PFY_LOCAL_RUNTIME=llama-swap`), `./pfy start` / `./pfy up` start `llama-swap` in the background if `:9292` is not already healthy, then wait for `GET /v1/models` or `/health`. Missing binary is an honest skip (one-liner), not fake ready. Still down after wait = partial.

When the detector selects llama-server (or `PFY_LOCAL_RUNTIME=llama-server`), same for `:8080` if a GGUF path is set (`PFY_LLAMA_MODEL`, then `LOCAL_CODER_MODEL` as an existing file). No path, missing binary, or API still down: honest skip / partial. Do not download weights. Shimmy stays an echo stub.

## Map to old Make levers

| Simple | Make / script |
|--------|----------------|
| `pfy setup` | `make env-init` + `bootstrap/grok-cli/install.sh` |
| `pfy` / `pfy board` | native operator window (Tauri if built, else already-on-box webkit, else stdlib tk; `--open` browser hatch only) |
| `pfy start` / `pfy up` | unnamed: same native window. named `pfy start <id>`: inference + env-stage + exec that harness |
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
| **detected-stub** | Binary found but adapter still stub |
| **skip** | Honest skip (tape / unused engine) — never `unknown` |

Registry: [`data/harnesses.json`](../../data/harnesses.json).

## Stubs (honest)

`agent-cage` stays stubbed for start (`./pfy start agent-cage` is STUB + issue #62, exit 2). Docker on PATH is not ready. Optional personal lab: `./pfy stage --lab` maps to `make cage-doctor`, `cage-setup`, `cage-up-mcp`. Missing Docker is honest skip, not product-ready. Do not sell cage.

`exo` is an **optional lab** adapter when `exo.sh` is at `$ROOT/exo.sh`, `$HOME/exo/exo.sh`, or on PATH (`./pfy start exo` execs it; missing: STUB + issue #60 + official setup.sh one-liner, exit 2). Not the default harness. Not a Grok replacement. `./pfy harness use exo` does not change `default_harness` (stays grok). Do not vendor Exo. Personal lab-IT only.

Continue is a **config recipe** at `bootstrap/continue/` (`LOCAL_OPENAI_BASE_URL`, not Ollama-only). `./pfy start continue` stays STUB exit 2. Continue is never detected-stub. If continue or agent-cage is the active harness, bare `./pfy` / unnamed start is FAIL with no grok/opencode fallback; copy `pfy harness use grok`.

The native operator window **is** the main interface (`./pfy` with no args, `./pfy board`). Tauri 2 binary when `gui/operator/src-tauri/target/{release,debug}/pfy-operator` exists; else already-on-box webkit (`scripts/pfy-gui.py`) wrapping the same frontend; else stdlib tk with live chips from `./pfy status`. pywebview is PFY_GUI_DEV=1 only. The window always opens. Optional `./pfy board --open` is a browser hatch, not the main path. In-window attach for grok/opencode spawns a sidecar. continue/agent-cage active: FAIL + copy `pfy harness use grok` (no fallback). Consultants should eval board chips against the `./pfy status` live column (same host; `missing` not `unknown`). Grok chip is PATH-only. nimo banner only if hostname contains `nimo`. Board is not a supervisor.

`gemini` is a live adapter when `gemini` or `gemini-cli` is on PATH (`./pfy start gemini` execs it; missing: STUB + issue #59 + official install one-liner, exit 2). Login/credentials/2FA are owner-only.

`codex` is a live adapter when `codex` is on PATH (`./pfy start codex` execs it; missing: STUB + issue #58 + official install one-liner, exit 2). Login/credentials/2FA are owner-only.

`claude-code` is a live adapter when `claude` is on PATH (`./pfy start claude-code` execs it; missing: STUB + issue #57 + official install one-liner, exit 2). Login/credentials/2FA are owner-only. Optional skills-external path is documentation only.

`hermes` is a live adapter when `hermes` or `hermes-agent` is on PATH (`./pfy start hermes` execs it; missing: STUB + issue #56 + install one-liner, exit 2). `/hermes-feedback` stays process-only. `./pfy start <id>` prints `STUB harness: <id>`, the GitHub issue URL from `data/harnesses.json` when set, and **exits 2**. `./pfy status` / `harness list` show `stub` (or `detected-stub` if a binary is on PATH). A binary or Docker on PATH is **not** ready.

Patterns may already exist as skills/docs; the unified installer path does not. Progress tracked on GitHub under label `harness-adapter`.

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
| llama-swap / llama-server start | [#104](https://github.com/themark-net/pfy-mentat/issues/104) |
| board URL on start/up | [#106](https://github.com/themark-net/pfy-mentat/issues/106) |
| native operator GUI | [#108](https://github.com/themark-net/pfy-mentat/issues/108) |
| window always opens | [#114](https://github.com/themark-net/pfy-mentat/issues/114) |
| FreeToken `ft serve` health wait | [#110](https://github.com/themark-net/pfy-mentat/issues/110) |
| models pull live engine | [#112](https://github.com/themark-net/pfy-mentat/issues/112) |
