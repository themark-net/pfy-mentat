# Module: `./pfy` (`scripts/pfy`)

**Purpose:** Product door (G8 / ADR-0012). One CLI: setup, status, bare start = native operator window (inference → env-stage → window; no harness exec), named start still execs a harness, models inspect, harness select.

## Entry

```bash
./pfy                    # inference → env-stage → native window
./pfy help
./pfy setup [local-only|balanced|max-performance]
./pfy status
./pfy start [harness]    # no name: native window; named: exec that harness (Attach mode #208)
./pfy up                 # same as bare ./pfy
./pfy board [--open]     # alias of the native window (Tauri / webkit / tk); --open browser hatch only
./pfy harness list|use <id>|show [id]
./pfy models
./pfy models pull <name>    # live engine (FreeToken records; Ollama pulls; llama skip)
./pfy models recommend      # ranked host-fit models not yet pulled (#207)
./pfy models try [name]     # pull top/named recommendation — operate-or-FAIL (#207)
./pfy context              # OpenContext oc prove (#205); FAIL if node/oc missing
./pfy stage | eval | ship
```

Root `./pfy` is a 100755 wrapper that execs `scripts/pfy`. Detector is invoked with `bash`.

**Attach mode (#208):** HTML+tk select `bare` | `orchestration` | `code-graph`; paint `using: <mode>`. Named start and in-window Attach hand off skills/AGENTS/prompts/env or FAIL+next. [attach-mode.md](attach-mode.md).

**Recommend / try (#207):** Engine + `./pfy models recommend` ranks host-fit models not yet pulled. `try` pulls one FreeToken-first (operate-or-FAIL). Handoff: engine pin · Attach re-probe · TUI reload. [recommend-models.md](recommend-models.md).

## Not yet

- Health-wait + default-model complete for Ollama (`./pfy start` still fire-and-forget serve)
- Remaining harness adapters (hermes, claude-code, codex, gemini, exo, continue, agent-cage)
- Treating `./pfy models` as success
