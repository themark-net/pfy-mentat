# X intake 2026-10-16: handoff (Entries 122-124)

Daily X intake routine, window 2026-10-16 00:38Z to 2026-10-17 00:34Z (Mark's bookmarks plus the watch list). Three catalog entries at **I0** plus one stdlib smoke script, a folder README paragraph and three `.gitignore` lines for receipts. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. The previous slice #296 (119-121) is merged; `main` was `5d03edc` (after #297, the AgentDescent trial) with 121 as the highest entry when this branch was cut.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 122 | [llm-router](https://github.com/ypollak2/llm-router) (MIT, Python, 15.4.0) | Local, free-first router for coding-agent prompts with a deterministic offline classifier and local-only handling of prompts with secrets. **Possible eval-auto trial** vs `org-spinny-decide` for local-vs-escalate routing | Yes, venv under `tmp/`, Ollama as the local tier. Smoke PASSed on the Grok Bot box |
| 123 | [HarnessRouter CE](https://github.com/HarnessRouter/harnessrouter) (Apache-2.0, v0.34.2) | One self-hosted Responses-compatible API over Codex, Claude Code, Hermes, Pi and others (Unified Harness Protocol). Reference design for comparing harnesses | Not yet: Docker only (unconfirmed on nimo) and needs a provider key; local provider support unconfirmed. Not run anywhere |
| 124 | [Squadra](https://github.com/dagoSte/squadra) (MIT, stdlib Python, v3.10.1) | Local registry for multi-agent work: acknowledgements, scoped tasks, proof before close, independent review, fail-without-fix proof for defects | Yes, checkout under `tmp/`, Python 3.12+. Smoke PASSed on the Grok Bot box |

Files: `sources/entries/122-llm-router.md`, `123-harnessrouter.md`, `124-squadra.md`, `examples/x-intake-local/smoke_122_124.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py`; every child goes through `run_isolated`), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{llmrouter,harnessrouter,squadra}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_122_124.py --entry llmrouter|harnessrouter|squadra` should exit 2 with an operator reason until staged:

- llmrouter: `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/llm-router/.venv` then `.venv/bin/pip install llm-routing==15.4.0`. Never run `llm-router install` with the real HOME.
- squadra: `git clone --branch v3.10.1 https://github.com/dagoSte/squadra ~/DEVELOP/pfy-mentat/tmp/squadra`. Needs python3 >= 3.12. Don't run its installer.
- harnessrouter: only if Docker is already on nimo. If it isn't, leave this entry catalog-only; installing Docker is a nimo system change that needs Mark.

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap with no network where it applies): llmrouter PASS (classifier: simple query and code, both confident; `demo` exit 0 with its table; HOME empty); squadra PASS (init, two seats, one task; `doctor` integrity passed with `assign-T1` pending; `status` showed the task; repo clean; HOME empty). Negative paths: no binary or no checkout gives exit 2 for both; `$LLMROUTER_VERSION=9.9` and `$SQUADRA_VERSION=1.0.0` give 2; `PFY_XINTAKE_TIMEOUT=0.001` gives exit 1 with "python version timeout". harnessrouter: no docker gives 2. The harnessrouter happy path has **not** run anywhere (no Docker on the box); its endpoint path and the 401/403 expectation come from the README and may need a fix on first run. `python3 -m py_compile` is clean. `scripts/catalog_check.py` and the unit tests were not run in this slice (no checkout on the box); Tester should run them on the PR head.

## Findings worth knowing

- **llm-router turns on direct execution by default** (`LLM_ROUTER_DIRECT_EXECUTION`): the local model gets write, edit and run-command tools under an allowlisted path, which upstream says does not stop targeted deletes or exfiltration. Set it to `false` for any trial. `install` writes hooks into host configs under HOME and state into `~/.llm-router/`.
- **HarnessRouter CE needs a provider API key and Docker**, starts its Console with a default password, and shows its own API key once. Keep it on loopback, change the password, and put keys straight into a secret store.
- **Squadra's default registry is `~/.local/state/squadra/`**; pass `--root` under `tmp/`. `--lang` defaults to Italian. Hand edits to `events.jsonl` didn't change `doctor`'s verdict on the box, so the SQLite registry is the record.

## Recommended next steps (not started)

1. **Eval-auto trial: llm-router's offline classifier vs `org-spinny-decide`.** Collect 40-60 real org prompts labeled "local is fine" or "escalate" (from recent Build drop-ins and bot asks), score `classify_signals` against the current local gate on the same set, then try llm-router's Ollama tier with `qwen3.6:35b` on the "local" bucket. Measure agreement with the labels, wall time on nimo, and how often a secret-bearing prompt stays local. Direct execution off, temp HOME, no `install`.
2. Squadra: run one multi-seat Build session on a throwaway pfy-mentat worktree with a registry under `tmp/`, and compare its close/proof rules with what Tester and Reviewer check today.
3. HarnessRouter: only after Docker is confirmed and a local endpoint is confirmed as a provider. Otherwise keep it as the UHP reference.

## LATER (logged, not cataloged this run)

- **KYB** (@DanKornas, MIT, Rust). Git-backed shared memory and incident tracker for agent fleets, local e5-small embeddings. Overlaps Entry 120 (Kenfold); compare if a shared-memory trial starts.
- **SolonGate Agent Security** (@DanKornas, Apache-2.0, Go). Local policy gateway for agent tool calls with secret detection and audit log. Overlaps destructive_command_guard in the toolsets drop-in.
- **RepoBrain** (@DanKornas, MIT). Repo knowledge engine for grounded codebase Q&A. Overlaps codebase-memory-mcp, Graphify and Entry 121.
- **fastCRW** (@DanKornas, AGPL-3.0, Rust). Firecrawl-compatible scrape/crawl/search engine with an MCP server. AGPL; revisit if agents need web data locally.
- **UseAgent** (@DanKornas, AGPL-3.0). Self-hosted isolated workspaces for Claude Code, Codex and OpenCode. Overlaps Entry 123 and the Build worktree flow.
- **Autonomous Company** (@DanKornas). Recurring autonomous work cycles around a shared summary. Overlaps the orchestrator loop skill.
- **Token Monitor** (@DanKornas). Local desktop widget for token usage across coding tools; Grok tools not listed, so little help for the #274 usage log.
- **Awesome AI Agent Attacks** (@DanKornas). Dated timeline of real agent security incidents; reading list for guardrail work, not a tool.
- Gateways overlapping the existing LiteLLM example: **Shepherd Model Gateway**, **Otari** (mozilla-ai), **LLM Gateway**, **Doubleword Control Layer**.
- @yume_arasaki mentioned running OMP and a modified Grok CLI against local models; no artifact posted. Worth watching for a write-up.

SKIPPED: q-agent-harness (no license), Chainloop (SDLC governance platform, heavy), Open Agent Connector, Cindy, Dodaios, Ankole, Dust, GenAssist, TomoriBot (agent clients and platforms off our stack), Index-1.9B (older small model), SGLang (already in TOOLS.md), OpenCode (already cataloged), oneDNN and tt-metal (hardware libraries not aimed at Strix Halo), dsh-plugin-guide (DeepSeek Harness plugins), Reverse Engineering Assistant, PersonaForge, explainroo, Langchain.rb, PolyglotMind, RikkaHub, MockServer, LandPPT, TrendRadar, OpenBiliClaw, Awesome MCP Servers (directory), MOSS Image and its 8-step finetune, the MiniMax H3 character-swap LoRA (image models), Nebula promos, robotics funding, GPU price notes, and news or opinion posts. @tom_doerr's how-to-train-your-gpt guide was left to Mark's weekly tom_doerr automation. One new bookmark (a vibe-coding launch checklist) is opinion, no tool.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector and raw URLs). No accounts, sign-ins, paid keys or spend. llm-router and Squadra ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model or agent CLI was started.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 122-124 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| llm-router or Squadra writes to the real HOME | `~/.llm-router` or `~/.local/state/squadra` appears on nimo | The smokes FAIL if their temp HOME is written; trials use `--root` and temp HOMEs |
| HarnessRouter smoke happy path untested | Fails the first time Docker is there | Treat the first run as the real test; fix the smoke in a follow-up |
