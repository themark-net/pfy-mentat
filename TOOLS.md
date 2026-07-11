# Master Tools Catalog

This file contains the detailed, living table of evaluated local LLM development tools. Each entry includes scores per stage, overall tier, key attributes/tags, GitHub link, and integration notes especially relevant to Grok CLI, MCP code memory, DSPy/LiteLLM patterns, and continuous pipelines.

**How to read scores**: See CATEGORIZATION.md for full rubric. Scores are initial estimates based on public docs, known usage in agentic coding workflows, and ecosystem signals as of 2026-07-11. They will be updated with empirical integration data. Paper-based entries include feasibility analysis.

**Legend**:
- **S1**: Stage 1 Core LLM/Agent Compatibility (weight 35%)
- **S2**: Stage 2 Perf/Efficiency (25%)
- **S3**: Stage 3 Pipeline/Extensibility (25%)
- **S4**: Stage 4 Ecosystem (15%)
- **Overall**: Weighted 0-100

## Active Catalog

| Tool | Primary Cat | GitHub | S1 | S2 | S3 | S4 | Overall | Tier | Key Tags | Integration Notes / Grok CLI / MCP |
|------|-------------|--------|----|----|----|----|---------|------|----------|-------------------------------------|
| **Grok CLI bootstrap** | Pipeline & CI/CD Components | this repo (`bootstrap/grok-cli/`) | 95 | 90 | 98 | 88 | 94 | S | #grok-cli #mcp-compatible #code-memory #pipeline #local-first | **First-party integration.** Idempotent `install.sh` reinstalls portable skills (`adr`, `docs`, `open-questions`, `karpathy-guidelines`), wires `codebase-memory` MCP + memory config, registers ponytail via `skills.paths`. Replay on any new host after Grok binary install. See bootstrap/grok-cli/README.md. |
| **codebase-memory-mcp** | Memory & RAG Systems | https://github.com/DeusData/codebase-memory-mcp | 92 | 88 | 95 | 85 | 91 | S | #mcp-compatible #code-memory #local-first #rag | Persistent code-graph MCP server used by Grok for project index / ADR hooks. Binary via official install.sh; this catalog owns Grok `config.toml` wiring through bootstrap (`--with-codebase-memory`). Captured pin: `ee68144`. |
| **LiteLLM** | Proxy & Routing | https://github.com/BerriAI/litellm | 95 | 85 | 98 | 90 | 93 | S | #litellm-ready #openai-shim #grok-cli #multi-llm #proxy | Critical unification layer. Route Grok API + local Ollama/MLX + fallbacks in one client. Excellent for agent loops. Native MCP? Easy to wrap. Docker ready. Top priority for any hybrid pipeline. |
| **Ollama** | Inference & Serving | https://github.com/ollama/ollama | 90 | 88 | 95 | 95 | 92 | S | #local-first #consumer-hw #openai-shim #tool-calling #apple-silicon #nvidia | Default local backend. Simple `ollama run` + REST API. Tool calling improving rapidly. Perfect entry for Grok CLI (set base_url). Strong community. MCP memory can be layered on top via custom tools or embeddings. |
| **Continue.dev** | Coding & Dev Agents | https://github.com/continuedev/continue | 92 | 80 | 92 | 88 | 90 | S | #ide-integration #coding-agent #local-first #tool-calling #vs code | Best-in-class IDE surface for local models. Autocomplete + chat + edit with codebase context. Can call tools. High synergy with MCP code memory (index repo symbols). GitHub Actions integration possible for CI evals. |
| **Aider** | Coding & Dev Agents | https://github.com/paul-gauthier/aider | 88 | 82 | 85 | 90 | 87 | A | #terminal #git-native #coding-agent #local-first #headless | Excellent terminal/git-aware coding agent. Works great with Ollama. Strong at iterative editing. Easy to script in pipelines. Lower IDE friction than Continue for some workflows. Good MCP target (repo as context). |
| **DSPy** | Agent Frameworks & Orchestration | https://github.com/stanfordnlp/dspy | 85 | 75 | 90 | 85 | 85 | A | #agentic #optimizer #pipeline #litellm-ready #reasoning | Systematic programming of LM pipelines. Optimizers (BootstrapFewShot, MIPRO) dramatically improve reliability. Pairs perfectly with LiteLLM for local + Grok. High value for gom-jobbar style agents. MCP memory can feed into DSPy modules. |
| **llama.cpp** (server mode) | Inference & Serving | https://github.com/ggerganov/llama.cpp | 85 | 95 | 80 | 85 | 88 | A | #high-perf #quantized #gguf #openai-shim #cpu-gpu | Ultimate performance/quantization control. GGUF ecosystem is massive. Server has OpenAI compat. Slightly more setup than Ollama but unmatched speed/footprint on consumer HW. Good base for custom agents. |
| **MLX + MLX-LM** | Inference & Serving | https://github.com/ml-explore/mlx (mlx-lm) | 80 | 92 | 78 | 80 | 82 | A | #apple-silicon #high-perf #quantized #local-first | Best-in-class on Apple Silicon (M-series). Fast unified memory, 4/8-bit native. mlx-lm provides server. Excellent for Mac-based dev pipelines. Tool calling via adapters. |
| **LangGraph** (LangChain) | Agent Frameworks & Orchestration | https://github.com/langchain-ai/langgraph | 82 | 70 | 88 | 88 | 82 | A | #agentic #graph #orchestration #tool-calling #rag | Stateful multi-actor agent graphs. Excellent for complex pipelines. Can use local Ollama via LangChain integration. Strong RAG/memory support (can integrate MCP). More boilerplate than DSPy for simple cases. |
| **Open WebUI** | UI & Interfaces | https://github.com/open-webui/open-webui | 75 | 80 | 85 | 92 | 82 | A | #ui #chat #local-first #docker #multi-model | Polished ChatGPT-like UI for local models (Ollama, llama.cpp, etc.). Supports tools in recent versions. Great for human-in-loop debugging of agents before headless pipeline use. Docker one-liner. |
| **Chroma** (or LanceDB) | Memory & RAG Systems | https://github.com/chroma-core/chroma | 70 | 85 | 80 | 85 | 78 | B | #rag #vector #code-memory #local-first #embeddings | Solid local vector DB. Easy Python SDK. Good for code RAG (embed functions/classes). Can serve as foundation for MCP-style persistent code memory. Lightweight. |
| **Atomic Task Graph (ATG)** | Agent Frameworks & Orchestration | Paper: https://arxiv.org/abs/2607.01942 (no code repo found) | 88 | 75 | 90 | 60 | 82 | A | #agentic #graph #dag #planning #parallelism #failure-repair #paper-based | Research framework using explicit DAGs for task decomposition instead of linear chains. Enables parallelism, verified result reuse, and localized repair on failures. Strong conceptual alignment with MCP (explicit dependencies/memory) and DSPy/LangGraph orchestration. No implementation code available; paper-only. **Feasibility of re-implementation: 75/100**. Straightforward: DAG construction (NetworkX), recursive decomposition via LLM prompts, parallel execution (concurrent.futures or LangGraph). Challenging: Sophisticated failure localization using graph history and robust intermediate result caching/reuse. Distilled core method: 1) Recursively decompose task into atomic subtasks forming evolving DAG sequence with explicit I/O dependencies. 2) Execute ready independent branches in parallel. 3) On failure, use graph evolution history to localize and repair only affected subgraph, preserving validated parts. High value for robust, efficient agent pipelines on small local models. Potential prototype: Extend LangGraph or DSPy with DAG state and repair logic. Watch for code release. |
| **ponytail** (skills pack) | Coding & Dev Agents | https://github.com/DietrichGebert/ponytail | 80 | 92 | 88 | 82 | 86 | A | #terminal #coding-agent #local-first #grok-cli | Minimalism / YAGNI skill pack for agents (`/ponytail`, audit, debt, review). Snapshot of `skills/` only vendored under `bootstrap/grok-cli/skills-external/ponytail` and registered via Grok `[skills].paths` (not copied into `~/.grok/skills`). Pin at capture: `8e69b4a`. |
| **karpathy-guidelines** | Coding & Dev Agents | https://github.com/forrestchang/andrej-karpathy-skills | 78 | 95 | 85 | 80 | 84 | A | #coding-agent #grok-cli #local-first | Single MIT skill: think-before-coding, simplicity, surgical diffs, goal-driven verification. Vendored into bootstrap first-party skills (pin `2c60614`). Complements ponytail on anti-overengineering. |

## Paper Analysis Use Case (Recurring Workflow)

'Read a paper' is now a supported method for discovering and evaluating new agentic tools/methodologies (e.g., from X posts). Process:
1. Identify paper link (from X, search, etc.).
2. Initial pass: Check for any GitHub/code/dataset links in post, abstract, or full text (none found for ATG).
3. Deep read/summarize: Core architecture, planning/execution phases, key algorithms/innovations, benchmarks/results.
4. Distill value: Key ideas in actionable form (e.g., DAG-based planning with localized repair).
5. Feasibility scoring (0-100): Assess replicability in local stack (NetworkX + LangGraph/DSPy + Ollama/LiteLLM) — straightforward parts vs. challenges.
6. Add to catalog: New row in table above with scores, tags (#paper-based), notes including distilled methods and implementation guidance. Link back to x-posts.md.
7. Update sources/x-posts.md with analysis notes.
8. (Optional) Propose prototype in examples/ or integration experiment.

This extracts maximum value from research papers even without code, turning them into actionable insights or future implementation targets for the pipeline.

## Evaluation Notes & Known Gaps (v0.3)

- **Grok CLI Integration**: Most S/A tier tools above expose OpenAI-compatible endpoints or have LiteLLM support, making them immediately usable by setting `OPENAI_BASE_URL` or equivalent in CLI/agent config. LiteLLM + Ollama is the current recommended default stack for hybrid Grok + local. **Operator environment** is now replayable via `bootstrap/grok-cli/install.sh` (skills + MCP wiring).
- **MCP Code Memory**: **codebase-memory-mcp** is the active MCP code-graph server in the Grok stack (indexed projects, structural navigation, optional ADR mirror). Still complementary: Chroma/LanceDB for custom RAG experiments. ATG's explicit graph aligns conceptually with MCP goals.

- **DSPy + LiteLLM Synergy**: Strongly recommended starting point for new agent development. DSPy optimizers + LiteLLM router + Ollama backend gives reliable, tunable local agents with fallback to Grok when needed. ATG ideas can extend this.
- **Missing High-Value Candidates** (to be added in next pass): Continue.dev plugins ecosystem, specific GGUF agentic models (e.g. recent Gemma/Qwen coding variants), more memory options (Mem0, Zep local), evaluation harnesses (e.g. custom SWE-bench lite runners), and code implementations from papers like ATG when released.
- **Hardware Specificity**: Scores assume typical consumer setup (Apple M-series or NVIDIA RTX 30/40-series consumer). ARM/AMD or extreme low-RAM (<16GB) may shift S2 scores.
- **Paper-Based Entries**: Feasibility scores are rough estimates; actual implementation effort depends on prototype testing. ATG example demonstrates the process.

## Update Process

1. New X link, paper, or discovered tool → add to this table with initial scores + link to sources/x-posts.md entry. For papers: Follow 'Read a paper' workflow above.
2. Integration experiment (in examples/ or external gom-jobbar-grok4) → append empirical results to Notes column and adjust scores.
3. Major release of existing tool or paper code drop → re-score relevant stages.

*Table maintained manually through v0.3; future versions may parse from data/tools.json for automated dashboard or pipeline scoring. 'Read a paper' formalized as recurring use case. Grok CLI bootstrap is the first first-party integration package.*