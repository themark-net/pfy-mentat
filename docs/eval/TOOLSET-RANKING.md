# Toolset value ranking for pfy-mentat (2026-10-06)

**Scope:** what to integrate next, assuming **local models only on nimo** (Strix Halo, Ollama about 22 GB edge; `llama-server --no-mmap` edge ≥ 51 GB) and no paid keys besides Grok and Cursor. Active products: Leasegrid, pfy-mentat, Gom Jabbar (jobbar-master), Lotline, Practice Minder.
**Read:** `TOOLS.md`, `data/tool_integration_stages.json`, `data/toolsets.json`, `sources/x-posts.md`, `sources/entries/066–092`, `docs/dogfood/LOCAL-BENCH-*`, `~/DEVELOP/_vendor/*` READMEs. Nothing was installed or run for this ranking.

## Already integrated (not re-recommended)

codebase-memory-mcp (I2, `code-graph` toolset) · LiteLLM (I2 smoke) · Ollama (host runtime) · agent-cage (I3) · write-guard-mcp · Grok CLI + project-process bootstrap (I3) · ponytail, karpathy-guidelines, mattpocock skills (on `skills.paths`) · `/agent-loops` 8-exits port (`orchestration` toolset) · `/hermes-feedback` · Jev / CUA-S1-FORMS decision lane (#230) · OpenContext (`opencontext` toolset) · repowise and kolibri smokes · Laya (trial-ran, not promoted) · local-bench harness (Entries 089–092).

## Ranking

| # | Candidate | Value for pfy-mentat (local-only) | Effort | API key? | Status |
|---|---|---|---|---|---|
| 1 | **llama-server `--no-mmap` lane** (llama.cpp server mode) | Only way to run `qwen3-coder-next` (83.3 % on #230, vs 79.2 % for qwen3.6). Make it a named lane in `pfylib/hedge.py` / `eval-lanes.json` with start/stop + health, not a bench-only script. It also gives atg-framework an OpenAI-compatible target | S–M | No | Built in a bench only (`pipelines/dogfood/local-bench-4/run_nommap_server.sh`). Not a lane |
| 2 | **atg-framework (ATG)** | Typed DAG compile + localized repair for multi-step local loops. First use is a compile bench, then an opt-in `atg` loop kind. See [ATG-FRAMEWORK-EVAL.md](ATG-FRAMEWORK-EVAL.md) | M | No (Ollama / local) | Built and unit-green (35 tests). Live compile unproven. Catalog card stale |
| 3 | **DSPy optimizers on the #230 decision bench** | Tune the prompt / few-shot set for `qwen3.6:35b` on the 48 cases with a held-out split. It may close the gap to coder-next without the 51 GB load. Gom Jabbar already uses DSPy | M | No (`ollama_chat/…` via LiteLLM) | Idea (TOOLS.md A-tier row, not integrated) |
| 4 | **destructive_command_guard** | Guardrail for unattended local workers (`worker-monitor`, OpenCode + Ollama), next to write-guard. That matters more as bots hand bulk work to local models | S | No | Catalog row only (Entry 041) |
| 5 | **opencode-mem** | Persistent memory for the **worker** surface (OpenCode + Ollama), which the Grok-side tools don't cover | S–M | No (local vector DB) | Catalog row only (Entry 049) |
| 6 | **claude-mem** (adapt, not adopt) | Its SQLite FTS5 observation store + session summaries is the best memory design on disk. Port the store pattern into `/hermes-feedback`. Its runtime hooks are Claude-Code specific | M–L | Yes by default (Claude / Gemini / OpenRouter providers). Local only if the OpenRouter base-URL override points at llama-server, which is unverified | Vendored only (`_vendor/claude-mem`, 2026-07-06) |
| 7 | **llama.cpp ngram-mod** speculative decoding | Free decode speedup on repetitive code edits for the local worker. Pairs with #1 | S | No | Catalog row only (Entry 051) |
| 8 | **Bumblebee** | Read-only supply-chain + MCP-config scanner. Cheap cage probe that protects every vendored tool on this list | S | No | Catalog row only (Entry 069) |
| 9 | **OpenLobster** | Go single binary, Ollama / OpenAI-compatible, MCP client, graph memory (file or Neo4j), Telegram and Slack channels. Candidate to replace `openclaw-gateway`, whose 128k-ctx GLM loads keep stalling benches. Ops value, not core | M | No (Ollama provider) | Vendored only (`_vendor/OpenLobster`, 2026-03-27) |
| 10 | **LEANN** | Compressed local RAG over catalog + sources for `catalog-ask`, without a server vector DB | M | No | Catalog row only (Entry 052) |
| 11 | **kanbots** | Kanban fan-out of CLIs into worktrees. Could drive the Build drop-ins in `docs/build-dropins/`. Overlaps `/agent-loops` | M | No | Stage 0 passed (npx). I1 |

### Skip or hold

Graphify, Ix, Axon (CM is primary) · Memvid · MUE-X and Exo (unsafe as runtimes) · asm · claude-codex-settings · MCO (multi-provider review that assumes paid CLIs) · Antigravity-Manager · AgenC · career-ops (Gom Jabbar's optional vendor, not pfy) · `_vendor/openclaw` (actually an iRODS/sssd tree, not the agent) · Kronos, bip39, monero, sssd (unrelated).

## Per-product notes

- **Gom Jabbar:** #3 (DSPy) moves routine identify/fit work to local models (ROADMAP item 7). #6 memory pattern for sticky answers.
- **Leasegrid / Practice Minder / Lotline:** no tool on this list is on their critical path. They are founder-gated (RELEASE / Mark inputs). #4 and #8 protect the Build sessions that work on them.
- **pfy-mentat:** do #1, then #2 (bench), then #3. That order raises local-model quality before adding loop machinery.
