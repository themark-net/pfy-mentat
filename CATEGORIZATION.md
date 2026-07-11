# Categorization & Ranking Methodology

This document expands on the taxonomy and staged criteria introduced in README.md. It is intentionally versioned and will be refined via PRs as real usage data from integrations accumulates.

## 1. Primary Category Taxonomy

Each tool receives **one primary category** and **multiple secondary tags**.

### Inference & Serving
Runners and servers that host LLMs locally with an API.
- Examples: Ollama, llama.cpp (with server), MLX-LM, vLLM (local mode), LM Studio backend, GPT4All.
- Key eval axes: API compatibility (OpenAI), quantization options, hardware accel (CUDA/Metal/ROCm/Vulkan), multi-model support, context length stability.

### Agent Frameworks & Orchestration
Systems for building multi-step, tool-using, reasoning agents and pipelines.
- Examples: LangGraph, DSPy, CrewAI, AutoGen, Haystack, LlamaIndex workflows, custom ReAct/Plan-and-Execute loops.
- Key eval axes: Native tool calling quality, graph vs linear orchestration, optimizer support (DSPy), state/memory management, ease of adding custom tools.

### Coding & Dev Agents
Specialized agents for software engineering tasks (autocomplete, edit, chat, PR generation, terminal execution).
- Examples: Continue.dev, Aider, OpenDevin, Cline/Roo Code, Cursor (local mode), Windsurf, etc.
- Key eval axes: Git integration, IDE surface quality, success rate on real coding tasks (SWE-bench lite proxies), context management for large codebases, MCP/code memory synergy.

### Memory & RAG Systems
Components for persistent memory, vector search, and retrieval-augmented generation, especially code-aware.
- Examples: Chroma, FAISS, LanceDB, PGVector, Mem0, Zep, custom SQLite + embedding pipelines, MCP implementations.
- Key eval axes: Ingestion speed for code, retrieval precision/recall on code symbols, long-term session persistence, integration with agent loops.

### Tool Calling & Function Infrastructure
Low-level or protocol-level support for models to call external functions/tools reliably.
- Examples: Native OpenAI tool calling in inference servers, MCP (if protocol), function calling harnesses in agent frameworks, JSON schema validators.
- Key eval axes: Schema adherence rate, parallel tool calls, error recovery, streaming tool results.

### UI & Human-in-the-Loop Interfaces
Frontends for interacting with local agents/models.
- Examples: Open WebUI, SillyTavern, AnythingLLM, custom Streamlit/Gradio dashboards, VSCode extensions.
- Key eval axes: Chat UX, tool visualization, agent trace inspection, multi-model switching.

### Optimization & Quantization
Libraries and techniques for making models smaller/faster on local hardware.
- Examples: bitsandbytes, GGUF (llama.cpp), AWQ/GPTQ (AutoGPTQ), MLX 4/8-bit, speculative decoding, pruning.
- Key eval axes: Quality vs size trade-off on coding/reasoning benchmarks, inference speed uplift, VRAM reduction.

### Evaluation & Benchmarking
Tools and harnesses for measuring agent/tool/model performance.
- Examples: Custom scripts using HumanEval, MBPP, SWE-bench subsets, agentic task suites (WebArena, ToolBench), latency/throughput profilers, cost (even if local: tokens/sec, RAM).
- Key eval axes: Reproducibility, coverage of agentic behaviors, correlation with real dev productivity.

### Proxy & Routing
Unified interfaces that abstract multiple backends (local + remote).
- Examples: LiteLLM (core strength), custom routers, OpenRouter local shims.
- Key eval axes: Fallback reliability, load balancing, logging/observability, cost tracking (even local), streaming support.

### Pipeline & CI/CD Components
Infrastructure for continuous integration, testing, and deployment of LLM-powered tools.
- Examples: GitHub Actions workflows that spin up Ollama + run agent evals, Docker Compose for full stacks, monitoring (Prometheus + local LLM), ArgoCD local manifests.
- Key eval axes: Idempotency, secret management for local, reproducibility of agent runs, integration with repo (this one).

## 2. Cross-Cutting Tags (apply multiple)

- `#local-first` `#airgapped` `#consumer-hw` `#nvidia` `#apple-silicon` `#amd`
- `#tool-calling` `#structured-output` `#agentic` `#reasoning`
- `#mcp-compatible` `#code-memory` `#rag`
- `#litellm-ready` `#openai-shim` `#grok-cli`
- `#github-actions` `#docker` `#k8s`
- `#high-perf` `#low-latency` `#quantized`
- `#ide-integration` `#terminal` `#headless`

## 3. Detailed Scoring Rubric (v0.1)

Each stage scored 0-100 (or N/A if not applicable). Weighted sum as in README.

**Stage 0 Gate Criteria** (binary pass/fail, documented in Notes if fail but still tracked as "niche"):
- Self-hostable with <5 min setup on fresh Ubuntu/Mac
- License allows commercial/research use without copyleft issues for pipeline embedding
- At least one clear runnable "hello world" example or quickstart that exercises core feature

**Stage 1: Core LLM & Agent Compatibility (0-100)**
- 100: Native OpenAI tool calling + streaming + structured output on multiple strong models; proven in multi-turn agent loops
- 80: Good OpenAI shim or easy adapter; tool calling works on 1-2 recommended models with minor prompt engineering
- 60: Basic chat completion only; tool calling via fragile parsing or external harness
- <40: No practical agent/tool use path

**Stage 2: Performance & Resource Efficiency (0-100)**
- Measured where possible on reference hardware (M3 Max 36GB, RTX 4090 24GB, or Ryzen 7950X + 64GB).
- Factors: tok/s for 7B/13B/32B Q4/Q5 on coding prompts, VRAM/RAM at 8k/32k context, cold start time, quantization quality delta (HumanEval or similar).
- Bonus for excellent Apple Silicon / Metal or Vulkan support.

**Stage 3: Pipeline Integration & Extensibility (0-100)**
- 100: Docker one-liner or compose, native plugin system or easy Python SDK, documented MCP/custom memory hook, GitHub Action example exists or trivial to write
- 80: Good Python/JS SDK, Docker support, clear extension points
- 60: Works in scripts but requires custom glue code; limited docs on integration
- Low: Monolithic or closed extension model

**Stage 4: Ecosystem (0-100)**
- Stars + recent activity (last commit <30d or active fork with momentum)
- Docs quality (API ref + tutorials + troubleshooting)
- Community signals (Discord responses, issue close rate, third-party blog posts)
- Bonus for existing adoption in similar dev/agent projects

## 4. Tier Definitions

- **S-Tier (90-100)**: Core infrastructure. Integrate immediately into primary pipelines. Minimal friction, high leverage.
- **A-Tier (80-89)**: Strong complementary component. High value in specific niches or as secondary in stack.
- **B-Tier (65-79)**: Useful for specific tasks or experimentation. May require more glue.
- **C-Tier (50-64)**: Niche or early-stage. Track for future improvements or as fallback.
- **D / Watch**: Gate issues or low scores but interesting idea. Re-evaluate on major releases.

## 5. Refinement Process

- New tool added → initial quick score by maintainer + open Issue for community scoring.
- After integration attempt (e.g. in examples/ or personal gom-jobbar style agent) → update scores with empirical data (success rate, tokens/sec, memory fidelity, dev velocity impact).
- Quarterly review of weights if pipeline outcomes show certain stages under/over-weighted.
- When a tool from an X post is added, link back to the post in sources/x-posts.md and in the tool's Notes.

This system prioritizes **actionable integration** over pure benchmark chasing. A tool that is 5% slower but 3x easier to wire into a Grok CLI + MCP + GitHub Actions pipeline will outrank a theoretically superior but integration-hostile alternative.