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
./pfy catalog               # usable catalog browse subset (#209)
./pfy catalog ask [name]    # ask attached TUI to implement for next launch
./pfy catalog queue [name]  # REAL GitHub issue Design→DevBot (#214)
./pfy catalog status        # queued items + open/closed/PR
./pfy launch               # Loop wizard Launch session (#225)
./pfy context              # OpenContext oc prove (#205); FAIL if node/oc missing
./pfy code-graph           # Axon prove or codebase-memory equivalent (#215)
./pfy axon                 # alias of code-graph
./pfy stage | eval | ship
```

Root `./pfy` is a 100755 wrapper that execs `scripts/pfy`. Detector is invoked with `bash`.

**Attach mode (#208 / #213 / #215):** HTML+tk select `bare` | `orchestration` | `code-graph`; paint `using: <mode>`. Orchestration starts a multi-step local loop (prove or FAIL+next) and Loop shows last evidence. Code-graph hands Axon or paints `path=codebase-memory (not axon)`. Named start and in-window Attach (OpenCode | Hermes | Grok | Codex | Claude) hand off skills/AGENTS/prompts/env or FAIL+next. [attach-mode.md](attach-mode.md) · [code-graph.md](code-graph.md).

**Attach Codex usable (#220):** HTML+tk **Attach codex** and `./pfy start codex` prove models list + one smoke on the FreeToken-first live base before attached paint / exec. Missing Codex is FAIL + installer, never a silent stub. [codex-adapter.md](codex-adapter.md).

**Attach Claude usable (#221):** HTML+tk **Attach claude** and `./pfy start claude` / `claude-code` prove models list + one smoke on the FreeToken-first live base before attached paint / exec. Missing Claude is FAIL + `npm install -g @anthropic-ai/claude-code`, never a silent stub. [claude-code-adapter.md](claude-code-adapter.md).

**Recommend / try (#207):** Engine + `./pfy models recommend` ranks host-fit models not yet pulled. `try` pulls one FreeToken-first (operate-or-FAIL). Handoff: engine pin · Attach re-probe · TUI reload. [recommend-models.md](recommend-models.md).

**Catalog ask / queue (#209 / #214):** Tools browse (usable subset, not scores-only). Ask attached TUI to implement for next launch (prompt/artifact). **Queue for org** creates a real GitHub issue and paints open/closed/PR. HOLD 70–75 not auto-lifted. [catalog-ask-queue.md](catalog-ask-queue.md) · [live-org-queue.md](live-org-queue.md).

**Launch wizard (#225):** Loop primary path is compose (runtime · lane · toolsets · harness) then **Launch session** into an enterable TUI, or FAIL+next. Attach X is secondary re-attach. Window stay-open. HTML+tk. No Env nav tab. [launch-wizard.md](launch-wizard.md).

## Not yet

- Health-wait + default-model complete for Ollama (`./pfy start` still fire-and-forget serve)
- Remaining harness adapters (gemini, exo, continue, agent-cage)
- Treating `./pfy models` as success
