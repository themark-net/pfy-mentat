# Master Tools Catalog

This file contains the detailed, living table of evaluated local LLM development tools. Each entry includes scores per stage, overall tier, key attributes/tags, GitHub link, and integration notes especially relevant to Grok CLI, MCP code memory, DSPy/LiteLLM patterns, and continuous pipelines.

**How to read scores**: See CATEGORIZATION.md for full rubric. Scores are initial estimates based on public docs, known usage in agentic coding workflows, and ecosystem signals as of 2026-07-11. They will be updated with empirical integration data.

**Legend**:
- **S1**: Stage 1 Core LLM/Agent Compatibility (weight 35%)
- **S2**: Stage 2 Perf/Efficiency (25%)
- **S3**: Stage 3 Pipeline/Extensibility (25%)
- **S4**: Stage 4 Ecosystem (15%)
- **Overall**: Weighted 0-100

## Active Catalog

| Tool | Primary Cat | GitHub | S1 | S2 | S3 | S4 | Overall | Tier | Key Tags | Integration Notes / Grok CLI / MCP |
|------|-------------|--------|----|----|----|----|---------|------|----------|-------------------------------------|
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

## Placeholder Entry - First X Seed Post

**Tool(s) from https://x.com/i/status/2075994424484732984** (pending extraction)

- **Status**: Awaiting post content or user-provided summary of mentioned repos/tools.
- **Action**: Once available, add dedicated row(s) above with full scoring pass. Likely an agentic GGUF model, new framework, or hardware/tool combo given timing and local LLM interest.
- **Suggested tags on addition**: #agentic #gguf #tool-calling (adjust after review)

## Evaluation Notes & Known Gaps (v0.1)

- **Grok CLI Integration**: Most S/A tier tools above expose OpenAI-compatible endpoints or have LiteLLM support, making them immediately usable by setting `OPENAI_BASE_URL` or equivalent in CLI/agent config. LiteLLM + Ollama is the current recommended default stack for hybrid Grok + local.
- **MCP Code Memory**: No tool has native "MCP" yet in this catalog (definition assumed custom or emerging protocol for model context persistence, especially code symbols/sessions). Recommended path: Use Chroma/LanceDB + custom ingestion of repo AST + session logs, exposed as tools to agents. DSPy modules or LangGraph state can persist to it. Future entry for any dedicated MCP server/impl.
- **DSPy + LiteLLM Synergy**: Strongly recommended starting point for new agent development. DSPy optimizers + LiteLLM router + Ollama backend gives reliable, tunable local agents with fallback to Grok when needed.
- **Missing High-Value Candidates** (to be added in next pass): Continue.dev plugins ecosystem, specific GGUF agentic models (e.g. recent Gemma/Qwen coding variants), more memory options (Mem0, Zep local), evaluation harnesses (e.g. custom SWE-bench lite runners), and any tools directly from the seed X post.
- **Hardware Specificity**: Scores assume typical consumer setup (Apple M-series or NVIDIA RTX 30/40-series consumer). ARM/AMD or extreme low-RAM (<16GB) may shift S2 scores.

## Update Process

1. New X link or discovered tool → add to this table with initial scores + link to sources/x-posts.md entry.
2. Integration experiment (in examples/ or external gom-jobbar-grok4) → append empirical results to Notes column and adjust scores.
3. Major release of existing tool → re-score relevant stages.

*Table generated/maintained manually in v0.1; future versions may parse from data/tools.json for automated dashboard or pipeline scoring.*