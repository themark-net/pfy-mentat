# X Post Sources Log

Log of X (Twitter) posts used to seed or expand the tool catalog. Each entry includes link, date (if known), poster, summary of content/tools mentioned, extracted GitHub repos, and link to corresponding entry in TOOLS.md or new tool creation.

This enables traceability from social signal to evaluated component.

## Entries

### Entry 001: Atomic Task Graph (ATG) - Agentic Planning Framework

- **URL**: https://x.com/i/status/2075994424484732984
- **Date**: 2026-07-11
- **Poster**: Alex Veremeyenko (@alex_verem / @alex_prompter)
- **Summary / Key Claims**: Discusses a new research framework called Atomic Task Graph (ATG) from Tsinghua and South China University of Technology researchers. ATG uses explicit directed acyclic graphs (DAGs) for task decomposition instead of linear chains, enabling parallelism, localized failure repair, and better performance with small 7B-8B models on agent benchmarks (e.g., outperforming GPT-4 + ReAct on ALFWorld). Emphasizes architecture over scale. Includes video explanation and links to the paper.
- **Extracted Repos / Tools**: None (research paper only). Paper: https://arxiv.org/abs/2607.01942. No GitHub code or implementation found in post or paper.
- **TOOLS.md Link**: Added detailed entry under Agent Frameworks & Orchestration with feasibility analysis and distilled methodology.
- **Notes**: Strong conceptual fit for agent orchestration and MCP-style memory (explicit dependencies and reuse). Recurring use case: 'Read a paper' for discovering new agentic methodologies. No immediate code to subtree; focus on re-implementation feasibility. High value for pipeline robustness.
- **Status**: Analyzed - paper-based entry (no code repo)

**Paper Analysis Process (New Use Case)**: 
1. Extract from X post or direct link.
2. Browse PDF/HTML for repo/code links (initial pass: none here).
3. Summarize methodology, distill core ideas.
4. Score feasibility of implementation in local stack (e.g., NetworkX + LangGraph/DSPy + Ollama).
5. Add to TOOLS.md with notes, tags, and potential integration points.
6. Update this log.

### Entry 002: ADR / process docs for coding agents (research sweep)

- **URL**: multiple (semantic + keyword search 2026-07-11) — e.g. https://x.com/martinfowler/status/2036467195538968695 , https://x.com/KingBootoshi/status/2062106571669446800 , https://x.com/santtiagom_/status/2069083778228552024 , https://x.com/therobertta_/status/2073845367784017939 , https://x.com/jbdamask/status/2075216922153566671
- **Date**: 2026-07-11 (search date)
- **Poster**: community aggregate (Fowler, practitioners using Claude/Codex, skill authors)
- **Summary**: Strong consensus that **in-repo ADRs** (Context / Decision / Consequences / Alternatives) improve multi-session agent alignment. Practitioners tell agents to maintain ADRs during architecture chats. Community Claude skills for ADR exist; classic tooling is **adr-tools** + template catalogs. No dominant “open questions parking lot” product for agents—markdown/issues fill that niche.
- **Extracted Repos/Tools**: adr-tools (https://github.com/npryce/adr-tools); ADR template collections; optional emerging enforcement (Mneme / Decision Guardian — watch list). Our response: **project-process** scaffold + skills, not a new platform.
- **TOOLS.md Link**: project-process bootstrap (S); adr-tools (B optional)
- **Notes**: Verdict recorded in ADR-0005 and `bootstrap/project-process/.../evaluation.md` — light framework sufficient.
- **Status**: Analyzed — process kit shipped under `bootstrap/project-process/`

### Entry 003: colibri - Extreme Low-Resource MoE Inference Engine

- **URL**: https://x.com/i/status/2075731830477877612
- **Date**: 2026-07-11
- **Poster**: @chenzeling4 (Zane Chen)
- **Summary / Key Claims**: Colibri runs GLM-5.2 (744B-parameter MoE, only ~40B active per token) on a laptop with 25GB RAM in pure C with zero dependencies. ~2,400-line C file core. Keeps dense part (~17B params) resident in RAM (~9.9GB at int4); streams routed experts from disk on demand. Provides CLI chat and OpenAI-compatible serve mode. No GPU, no BLAS, no Python runtime. Exceptional engineering for consumer hardware.
- **Extracted Repos / Tools**: https://github.com/JustVugg/colibri (core inference engine). Pre-converted int4 model weights available on HF (jlnsrk/GLM-5.2-colibri-int4). Recent Tauri desktop shell addition.
- **TOOLS.md Link**: Added new row in Inference & Serving category (A tier, overall 86). Detailed integration notes on low-RAM flagship model enablement, serve endpoint for pipelines, and speed tradeoffs.
- **Notes**: Highest-signal external X seed to date for the catalog. Enables practical local use of flagship-scale MoE without datacenter hardware. Zero-deps + pure C = excellent reproducibility and pipeline friendliness. S1 very high (consumer HW access to 744B-class reasoning). S2 reflects current disk-streaming speed limits (0.05–1+ tok/s; faster on high-end NVMe/M-series). Strong community validation via rapid stars and engagement. Pinned specific recent commit. Recommended next: empirical testing of serve mode with LiteLLM/Grok CLI, tok/s benchmarks on target hardware, and MCP context integration potential.
- **Status**: Processed and cataloged (initial scores applied; hands-on eval + score refinement queued)

### Entry 004: Marketing Skills v2.8.0 — marketing-council multi-expert skill pack

- **URL**: https://x.com/i/status/2076048436538048530
- **Date**: 2026-07-11
- **Poster**: Corey Haines (@coreyhainesco)
- **Summary / Key Claims**: v2.8.0 release of the Marketing Skills pack (now 47 skills total). New flagship skill: `/marketing-council` — pitches or reviews marketing strategies by convening a simulated board of 12 legendary marketers (Seth Godin, David Ogilvy, Alex Hormozi, April Dunford, Eugene Schwartz, Claude Hopkins, Gary Halbert, Russell Brunson, Rory Sutherland, Byron Sharp + others). Every session includes a designated dissenter for rigorous, balanced critique and to surface blind spots. The pack consists of modular `SKILL.md` files (with `references/` for advisor dossiers and cross-skill links) targeted at Claude but implemented as portable markdown prompts + structured workflows. Free & open source. Install via `npx skills add coreyhaines31/marketingskills` (or equivalent CLI). Includes demo video in the announcement post. Strong community signal (300+ likes, 600+ bookmarks on v2.8.0 post; repo ~37k stars).
- **Extracted Repos / Tools**: https://github.com/coreyhaines31/marketingskills (core repo). New skill directory: `skills/marketing-council/` containing `SKILL.md` (161 lines defining session modes: quick take / council session / full council; advisor bench with specific lenses; structured output expectations) and `references/advisors/` (individual .md dossiers for each legend). 46 other skills cover the full marketing stack (ab-testing, ad-creative, ads, ai-seo, analytics, cold-email, content-strategy, copywriting, cro, customer-research, launch, lead-magnets, marketing-ideas, marketing-plan, pricing, prospecting, etc.) with heavy internal cross-referencing.
- **TOOLS.md Link**: New row added under Agent Frameworks & Orchestration category (as high-signal prompt/skill pattern library). Primary value: the `marketing-council` architecture and clean SKILL.md + references/ format. **Explicit recommendation**: Port/adapt the council + dissenter pattern and advisor personas into local Grok CLI skills (modeled after existing `bootstrap/grok-cli/skills/ponytail/` and `karpathy-guidelines/`) or as a DSPy module / custom agent loop. This directly addresses single-perspective bias and hallucination in local LLM agent outputs. The modular skill format is directly compatible with the local skills system in this repo.
- **Notes**: Borderline for strict "local LLM" criteria (original execution path is Claude API; Stage 0 gate passes only on the prompt content itself being fully self-hostable and adaptable). However, the *ideas* and *structure* have high pipeline value for any LLM (local or hybrid). The dissenter mechanism and multi-lens council is a concrete, low-overhead way to improve reasoning quality without extra models. SKILL.md format mirrors the one used in `bootstrap/grok-cli/skills/`. High S4 (ecosystem) due to massive stars, recent activity (v2.8.0 Jul 2026), and practitioner adoption. Prioritize: (1) Extract/adapt marketing-council into a first-party local skill under bootstrap or examples/. (2) Test in gom-jobbar or personal agent for marketing/strategy tasks or general decision review. (3) Consider as template for other domain councils (e.g., engineering council, biohacking council). See full SKILL.md and advisor refs in the upstream repo for implementation details. Strong recurring "read a skill pack" workflow candidate.
- **Status**: Processed and cataloged (initial scores applied; local adaptation experiment added to TODO.md and open-questions/)

### Entry 005: Antigravity-Manager — AI account switcher & local API relay (Tauri v2 / Rust)

- **URL**: https://x.com/i/status/2076109541863989620
- **Date**: 2026-07-12
- **Poster**: Zane Chen (@chenzeling4)
- **Summary / Key Claims**: Antigravity-Manager solves the pain of juggling multiple AI tool accounts with one-click seamless switching. Core innovation: converts web sessions (from tools that rely on browser login) into standard API calls via a local relay/proxy. Rust-based backend, Tauri v2 desktop frontend for tiny binary size (~4MB in the refactor edition). Eliminates protocol and auth mess across providers. ~30K stars on the main repo. High engagement because developers are exhausted by repetitive login, quota tracking, and account rotation for AI coding/agent tools (Gemini, Claude, Antigravity ecosystem, etc.).
- **Extracted Repos / Tools**: Primary: https://github.com/lbjlaq/Antigravity-Manager (~30k stars, Tauri v2 + Rust/React or Vue, local API proxy/relay with OpenAI/Anthropic compatibility, quota monitoring, auto-switching, unlimited account pool, backup/migration). Refactor edition: https://github.com/Ariszn/Antigravity-Manager-tauri (pure Rust + Tauri v2 + Vue 3, even smaller footprint, cross-device seamless migration, process management). Features include real-time quota visualization, smart auto-switch on rate-limit/quota thresholds, AES encryption for credentials, and acting as a local gateway that normalizes web-based sessions into clean API endpoints.
- **TOOLS.md Link**: New entry added under Proxy & Routing category (with UI & Human-in-the-Loop notes). Explicit integration value for Grok CLI + LiteLLM pipelines: run the manager locally as account/relay layer; point agents to its local proxy endpoint for automatic rotation and normalized access without managing logins per provider.
- **Notes**: Same high-signal poster as colibri (Entry 003) — pattern of excellent, practical dev tooling posts. Strong local-first credentials (Tauri desktop app, Rust core, fully offline relay after initial setup). Directly complements LiteLLM (unified routing) by adding account-pool + session-to-API conversion layer on top. The local relay/proxy capability is high-value for any multi-backend setup (Grok + local Ollama + cloud fallbacks) where web-only tools or rate-limited accounts are in play. S1/S3 high because it exposes standard API while handling the messy auth/session part locally. S4 excellent (30k stars, active releases, solves widespread friction). Recommend: (1) Download/test the Tauri binary for operator workflow. (2) Wire its local relay into LiteLLM config or Grok CLI base_url for seamless multi-account use. (3) Monitor for MCP/hooks if the project exposes useful state (quota, active account) for agent memory. (4) Consider the refactor edition for minimal footprint. This + colibri from same author = strong signal on practical local AI infra.
- **Status**: Processed and cataloged (initial scores applied; proxy/relay integration experiment added to TODO / open-questions)

### Entry 006: repowise — context optimization layer for coding agents (token & file-read efficiency)

- **URL**: https://x.com/i/status/2076117959958053084 (link post); original discussion https://x.com/srishticodes/status/2075849201523523729
- **Date**: 2026-07-12 (link post); main post 2026-07-11
- **Poster**: Srishti (@srishticodes)
- **Summary / Key Claims**: repowise is an open-source context layer for coding agents (Claude Code, Codex, Cursor, VS Code). It prevents agents from reading dozens of irrelevant files by providing smart, targeted context. No API key or billing required. Claims dramatic efficiency gains vs baseline Claude Code: 27x token efficiency, 36% lower cost, 89% fewer file reads, 49% fewer tool calls. All numbers reproducible with harness included in repo. 3.5k+ stars, 50k+ pip installs, 30+ contributors. Simple install: `pip install repowise` then point at codebase.
- **Extracted Repos / Tools**: https://github.com/repowise-dev/repowise (main repo). Lightweight pip-installable Python package that acts as a context optimization / smart retrieval layer on top of existing coding agents. Works out-of-the-box with popular IDE/agent setups.
- **TOOLS.md Link**: Added under Coding & Dev Agents (with notes on overlap with codebase-memory-mcp and RAG patterns). Strong measurable impact on token usage and tool-call reduction — directly relevant to pipeline cost/performance goals.
- **Notes**: Some redundancy with existing entries (codebase-memory-mcp for code-graph memory; general coding agents like Continue/Aider/ponytail). However, repowise's specific value is its lightweight, drop-in context optimizer with published, reproducible benchmarks focused on reducing wasteful file reads and tool calls in agent loops. This aligns tightly with core repo goals: improving efficiency, lowering token costs, and making local/hybrid agent runs more practical. It can feed better context into memory systems or run alongside them. S1/S3 high for immediate usability with existing agents. S2 strong on measured efficiency gains. S4 solid (3.5k stars + pip adoption). Recommend: Evaluate as complementary layer (test token savings on real gom-jobbar or personal coding tasks); consider integration patterns with LiteLLM + local models or as a pre-filter before MCP/codebase-memory. Good candidate for empirical benchmarking in the eval harness (OQ-0002).
- **Status**: Processed and cataloged (initial evaluation complete; noted overlaps + unique benchmark-driven efficiency angle; integration test suggested in TODO)

### Entry 007: Jamon Holmgren Agentic Coding Setup (comprehensive workflow checklist)

- **URL**: https://x.com/i/status/2076001786700394610
- **Date**: 2026-07-11
- **Poster**: Jamon Holmgren (@jamonholmgren)
- **Summary / Key Claims**: Detailed dump of a production-grade agentic coding setup for reliable AI agents (Claude Code, Cursor, Codex, etc.). Emphasizes that missing structural pieces hurts results. Covers 18+ elements including AGENTS.md as router to skills/docs/tools; standard workflow doc/skill (recommends Matt Pocock skills); self-healing docs kept updated by agents; agents run/test/fix the app themselves; end-to-end tests and maintenance docs; custom linters with auto-fix or LLM-assisted fix; cross-agent reviews with different models/personas (maintainability, security, performance, AI smells); agent traces/worksheets committed with git tags for session continuity; automatic end-of-session feedback committed for periodic review; custom scripts in tools/bin folder (with docs on creating them); periodic commit sweeps; coding conventions doc; agent loop/night shift skill; task queue (e.g. TODOS.md or Linear CLI); false-confidence test audits; visual regression tests; automatic performance benchmarks and profiling; end-of-shift full validations.
- **Extracted Repos / Tools**: References Matt Pocock skills repo (https://github.com/mattpocock/skills) for workflow doc/skill. Main value is the comprehensive process/workflow checklist and best practices for robust agentic setups. No single new repo, but points to established patterns and tools.
- **TOOLS.md Link**: Added as workflow/process resource under Agent Frameworks & Orchestration (or dedicated Harness/Workflow Engineering note). Strong mapping to existing repo components (AGENTS.md, project-process, skills bootstrap, evaluation rubric, ADRs/open-questions).
- **Notes**: Extremely relevant and actionable for enhancing the repo's agent scaffolding, harness engineering (see Entry on Learn Harness Engineering), and practical pipeline robustness. Many ideas directly extend current artifacts: make AGENTS.md a true router + self-healing guidance; add traces/worksheets (complements ADRs); custom scripts and review personas; autonomous loops and benchmarks (ties to evaluation harness ideas). Highly recommended for synthesis into docs, new skills, and bootstrap templates. Aligns with self-hosted/local focus by providing concrete, implementable workflows.
- **Status**: Processed and cataloged (added as workflow resource; integration recommendations for AGENTS.md enhancement and new skills drafted/implemented)

### Entry 008: mattpocock/skills — Reusable agent skills for real engineering

- **URL**: https://github.com/mattpocock/skills (referenced in above post and widely recommended)
- **Date**: N/A (established repo, referenced 2026-07)
- **Poster**: N/A (high-signal reference in agentic workflow discussions)
- **Summary / Key Claims**: Popular collection of composable, reusable agent skills (markdown SKILL.md files) for "real engineering" workflows with AI coding agents (Claude Code, Cursor, etc.). Focuses on practical, controllable skills rather than heavy frameworks. Includes router skills (e.g. ask-matt), planning (grill-me, to-prd, to-issues, wayfinder), TDD, code review, handoffs, research, prototype, etc. Install via npx skills@latest add mattpocock/skills. Works across agents; emphasizes composability and user control.
- **Extracted Repos / Tools**: https://github.com/mattpocock/skills (main repo, tens of thousands of stars, active). Many individual skills for planning, implementation, review, and orchestration.
- **TOOLS.md Link**: Added under Agent Frameworks & Orchestration or Skills & Prompt Engineering. Strong ecosystem value; direct fit for bootstrap skills and workflow enhancement.
- **Notes**: Excellent complement to the Jamon Holmgren setup and harness engineering resources. Provides ready-to-use, battle-tested skills that can be vendored or referenced in this repo's bootstrap/grok-cli/skills/ and project-process. Highly recommended for cataloging and potential integration (e.g., examples or templates). Aligns with composable skills theme in the repo.
- **Status**: Processed and cataloged (dedicated entry added; recommended for skills bootstrap enhancement)

### Entry 009: 21 Claude $20 Plan Hacks — Context, Token & Prompt Optimization Workflow

- **URL**: https://x.com/i/status/2075807299638014212
- **Date**: 2026-07-11
- **Poster**: Ruben Hassid (@rubenhassid)
- **Summary / Key Claims**: Practical list of 21 hacks to maximize the $20/month Claude plan instead of upgrading to $100. Focuses on token efficiency, context management, prompt engineering, file handling, chat/workflow habits, model selection, and feature usage. Examples: Convert PDFs to Markdown before uploading; plan in chat before using coding features; use short, specific prompts and prompt libraries; edit previous messages instead of stacking corrections; trim long about-me files and summarize periodically; use Projects for recurring context and separate new topics into fresh chats; turn off unnecessary features by default; use cheaper models (Sonnet) for simple tasks and reserve Opus for heavy work; be specific with repo exploration; use voice input for richer prompts; understand rolling 5-hour limits and split usage; know tool strengths (e.g. Gemini for images, Grok for real-time search). Includes links to exact .md prompt files via free subscription/Notion.
- **Extracted Repos / Tools**: No new GitHub repo in the post. Main value is the curated list of efficiency hacks and workflow patterns (prompt libraries, context budgeting, summarization/reset strategies). Complements tools like repowise (token savings) and skills collections.
- **TOOLS.md Link**: Added under Context & Token Efficiency / Prompt Engineering & Skills (or cross-referenced in Agent Frameworks). Strong practical value for pipeline cost/token optimization and agent workflow robustness.
- **Notes**: Highly relevant despite being Claude-specific — the principles are universal for any LLM usage (local Ollama + hybrid setups, Grok CLI pipelines, agent loops). Directly supports repo goals around token efficiency (see repowise), context management (MCP, codebase-memory, RAG), prompt/skill engineering (Matt Pocock skills, marketing-council), and robust workflows (Jamon Holmgren setup, harness engineering). Many hacks translate to local agent instructions: better context curation to reduce re-reads, prompt libraries as reusable skills, periodic summarization for long sessions, specific scoping for coding agents, model routing. Can inspire new skills (e.g., context budget auditor, prompt library manager, smart summarizer/reset) or enhancements to AGENTS.md / project templates. Excellent complement to existing efficiency and scaffolding resources.
- **Status**: Processed and cataloged (added as workflow/efficiency resource; potential for new skills or AGENTS.md integration noted)

### Entry 010: gstack — Garry Tan's Open-Source Claude Code Multi-Specialist Setup (23 skills + power tools)

- **URL**: https://x.com/i/status/2075933298627383473 (and https://github.com/garrytan/gstack)
- **Date**: 2026-07-11 (post); repo launched ~March 2026
- **Poster**: Granite (@Granite0x) highlighting Garry Tan (@garrytan, YC President/CEO)
- **Summary / Key Claims**: Garry Tan open-sourced his personal "gstack" — a production-grade Claude Code loadout with 23 opinionated specialists (slash-command skills) + 8 power tools. It turns a single developer into a virtual engineering team (CEO, Designer, Eng Manager, QA, Security, Release Engineer, etc.) via structured workflows (Think → Plan → Build → Review → Test → Ship → Reflect). 121k+ stars, MIT license. Supports Claude Code and multiple other AI coding agents (Cursor, Codex CLI, OpenClaw, etc.) via adapters. Includes browser/QA tools, safety guardrails, cross-model review (/codex), persistent memory (GBrain), and team install mode.
- **Extracted Repos / Tools**: Primary: https://github.com/garrytan/gstack (MIT). 23+ slash-command skills embodying distinct roles and methodologies; power tools for orchestration, safety, browser automation, memory. Install via simple git clone + ./setup into ~/.claude/skills/ or equivalent for other hosts.
- **TOOLS.md Link**: Row **gstack** (A-tier). Integration is **docs-first** (T-0014): `docs/ops/gstack-role-recipes.md` + AGENTS.md role router — not a skills.paths full embed (ADR-0009).
- **Notes**: Role specialization + Think→Plan→Build→Review→Test→Ship→Reflect is the portable value. Complements marketing-council (T-0011 first-party), mattpocock paths subset (tdd/code-review/to-spec), one-shot, cage smokes. **Do not** clone full gstack into this catalog. **2026-07-12 deeper-port eval:** raw skills.paths blocked (Claude harness); comparison attrs in `docs/ops/gstack-skill-port-comparison.md`; single-skill recommendation = first-party **investigate** RCA method rewrite (T-0017), not rsync.
- **Status**: Triple-write complete; T-0014 docs recipes + deeper-port comparison shipped 2026-07-12

### Entry 011: agent-cage (PNNL) — Docker sandbox harness with MCP (operator-selected)

- **URL**: https://github.com/pnnl/agent-cage (discovery: GitHub search `agent-cage`; also considered cleatdev/cleat, chaserhkj/agent-cage)
- **Date**: 2026-07-12
- **Poster**: N/A (operator request; GitHub)
- **Summary / Key Claims**: Docker-based sandbox giving agents a full Ubuntu environment while the operator controls network access via mitmproxy policy, TLS inspection, domain whitelist, audit logs. Native **MCP** overlay (`mcp-servers.yaml`, compose). CLI `agentcage up [--mcp]`, shell, policy, dashboard. Harness-agnostic (Claude Code, Cline, LangGraph, custom agents). Images are versionable for reproducible integration tests — primary path for testing catalog tools in isolation.
- **Extracted Repos / Tools**: https://github.com/pnnl/agent-cage (pin develop `ea0cdb328683`). Related: https://github.com/cleatdev/cleat (Claude-focused Docker cage), https://github.com/chaserhkj/agent-cage (Podman/microVM Rust CLI).
- **TOOLS.md Link**: agent-cage (PNNL) S-tier Pipeline row; wrapper `harness/agent-cage/`.
- **Notes**: Aligns with prior multi-dev harness experience (containers + MCP; Make optional for OS branching). Prefer pnnl for MCP + policy + compose; optional Makefile wrapper for Linux/macOS/Windows(WSL) developer ergonomics.
- **Status**: Processed and cataloged; harness package scaffolded under `harness/agent-cage/`

### Entry 012: Multica — Open-Source Managed Agents Platform (Human + AI Teammates)

- **URL**: https://x.com/i/status/2075999281996312951 (and https://multica.ai/, https://github.com/multica-ai/multica)
- **Date**: 2026-07-11 (post)
- **Poster**: Simplifying AI (@simplifyinAI)
- **Summary / Key Claims**: Multica turns coding agents into real teammates. Assign issues to an agent like you'd assign to a colleague — they'll pick up the work, write code, report blockers, and update statuses autonomously. No copy-pasting prompts. No babysitting runs. Your agents show up on the board like real team members, participate in conversations, and compound reusable "Skills" (SKILL.md packs) over time. 100% Free & Open Source. Works with Claude Code, Codex, OpenCode, OpenClaw, Hermes, Copilot, Cursor, and 14 total coding tools/agents. Strong focus on human + agent collaboration and skill compounding.
- **Extracted Repos / Tools**: Primary: https://github.com/multica-ai/multica (~39.6k stars, MIT/modified Apache). Go backend + Next.js/Electron frontend + CLI/daemon. Features: agent profiles on board, issue assignment & autonomous execution, unified activity timeline, reusable Skills library, runtime monitoring for local daemons, Docker self-host. Supports local daemon driving installed AI coding tools; cloud option available.
- **TOOLS.md Link**: Row **Multica** under Agent Frameworks & Orchestration (tier A, overall 88). `data/tools.json` object `Multica`; pin `2a48ffa2aa73`.
- **Notes**: Outstanding complement to gstack (Entry 010) and other agentic/harness entries. gstack excels at role-specialized slash-command skills and internal workflows; Multica adds the project management board, issue assignment, human+agent timeline, and skill compounding abstraction on top. Strong overlap in supported agents (Claude Code, Codex, Cursor, OpenClaw, etc.) but Multica's "teammates on the board" model reduces redundancy while enabling hybrid teams. Low redundancy risk; highly synergistic. Fits evaluation criteria well: high workflow relevance, Docker self-host, multi-agent surface. Does **not** replace agent-cage (isolation lab). Recommend: catalog done; optional later self-host smoke; explore skill interoperability with bootstrap/gstack patterns. Not a Grok-first requirement for core stack.
- **Status**: **Triple-write complete** (x-posts + TOOLS.md + tools.json) 2026-07-12

### Entry 013: Spec Kit — GitHub's Spec-First Structured Workflow for Agentic Coding

- **URL**: https://x.com/i/status/2076005136736850402 (and https://github.com/github/spec-kit)
- **Date**: 2026-07-11 (post)
- **Poster**: angel (@angeldot_)
- **Summary / Key Claims**: GitHub's Spec Kit solves "vibe coding" problems with AI agents. Forces the AI to create a structured specification BEFORE touching code: /constitution (rules/standards) → /specify (what to build) → /clarify (questions) → /plan (architecture/stack) → /tasks (ordered tasks) → /implement (execution). Reduces absurd errors, inconsistent code, and unpredictable results when working with agents. 120K+ stars, 10K+ forks, open source. Compatible with Claude Code, Cursor, Copilot, Codex, Gemini CLI, and +25 agents.
- **Extracted Repos / Tools**: Primary: https://github.com/github/spec-kit (120K+ stars). CLI-driven spec-first pipeline that agents must follow before any implementation.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Structured Workflow & Prompt Engineering. High-signal GitHub-backed workflow guardrail.
- **Notes**: Excellent complement to gstack (Entry 010) and Multica (Entry 012). Provides the mandatory "spec/planning guardrail" layer before code is touched. Strong overlap in supported agents (Claude Code ecosystem) but solves the predictability/vibe-coding pain point directly. Low redundancy risk — it's a process enforcer that improves results for all downstream tools (gstack skills, Multica assignment, etc.). High fit for evaluation criteria: Very High Workflow Relevance (Planning + Implementation), High Integration Ease (works with many cataloged agents), High Reproducibility (open source CLI commands + GitHub backing), Low Redundancy. Perfect for the repo's "reproduction of best practices" goal — provides a reproducible, spec-driven agentic coding workflow. Recommend: (1) Catalog as core structured workflow tool. (2) Strong candidate to pair with gstack + Multica for end-to-end planning-to-shipping reproduction templates. (3) Consider as baseline for enhancing our own AGENTS.md or project-process docs.
- **Status**: Processed and cataloged (added as major structured workflow resource; high priority for evaluation strategy integration)

### Entry 014: Karpathy Second Brain / Obsidian + Claude Code Wiki (Personal Knowledge Compounding Workflow)

- **URL**: https://x.com/i/status/2076163893983096970
- **Date**: 2026-07-12 (post)
- **Poster**: CyrilXBT (@cyrilXBT) highlighting Andrej Karpathy's idea
- **Summary / Key Claims**: Use AI (Claude Code) to build a "second brain" / living personal wiki instead of just writing code. Point Claude Code at an Obsidian vault folder. Drop sources (articles, transcripts, PDFs) into a `raw` folder. Claude ingests, links, files into a `wiki` of interconnected pages. Compounds over time. Setup: Install Obsidian, create vault, open in Claude Code, paste Karpathy's wiki idea, let Claude build folders + CLAUDE.md router. Then "ingest this" for new sources and query across everything. Never start from blank chat again. 5-minute setup.
- **Extracted Repos / Tools**: No new standalone repo (uses Obsidian + Claude Code). Pattern: folder-based vault with `raw/`, `wiki/`, and `CLAUDE.md` as the control file. Simple ingestion command + cross-query capability.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Personal Knowledge Management & Second Brain Workflows (or cross-referenced under Context & RAG patterns). Lightweight, high-signal personal workflow.
- **Notes**: Excellent lightweight complement to gstack (Entry 010), Multica (Entry 012), and Spec Kit (Entry 013). Uses similar CLAUDE.md router pattern as gstack but for personal knowledge compounding instead of engineering roles. Strong overlap with skills ingestion ideas and context management goals. Low redundancy — it's a simple, reproducible personal RAG/wiki setup using tools we already track (Claude Code + folder structure + Obsidian). High fit for evaluation criteria: High Workflow Relevance (Knowledge Management + Context building), Very High Integration Ease (uses existing agents + Obsidian), Very High Reproducibility (5-min setup with clear steps), Low Redundancy. Perfect for the repo's reproduction goal — easy to document as a best-practice personal second brain template. Recommend: (1) Catalog as core personal knowledge workflow. (2) Strong candidate for a simple reproduction script/template in the repo. (3) Synergistic with gstack-style CLAUDE.md patterns and Multica skill compounding.
- **Status**: Processed and cataloged (added as lightweight personal knowledge workflow resource; high value for practical reproduction)

### Entry 015: claude-code-monitor — Real-time Dashboard for Multiple Claude Code Sessions

- **URL**: https://x.com/i/status/2076022130802622814 (and https://github.com/onikan27/claude-code-monitor)
- **Date**: 2026-07-11 (post)
- **Poster**: Tom Dörr (@tom_doerr)
- **Summary / Key Claims**: Real-time dashboard for monitoring multiple Claude Code sessions. Useful for juggling several agent sessions without losing track of status, progress, or outputs. Clean, practical dev tooling for multi-session workflows.
- **Extracted Repos / Tools**: Primary: https://github.com/onikan27/claude-code-monitor. Real-time monitoring dashboard focused on Claude Code (and extensible to similar agents).
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Monitoring & Observability. Practical multi-session dashboard.
- **Notes**: Strong complement to gstack (Entry 010), Multica (Entry 012), and multi-agent workflows. Provides the missing real-time visibility layer for running multiple sessions in parallel. Low redundancy — it's focused observability, not full orchestration or skills. High fit for evaluation criteria: High Workflow Relevance (Monitoring multi-session agent work), High Integration Ease (Claude Code focused, easy to adopt), High Reproducibility (open source GitHub repo), Low Redundancy. Excellent for practical multi-agent setups. Recommend: (1) Catalog as monitoring tool. (2) Good addition for harness / multi-session reproduction templates. (3) Synergistic with gstack/Multica for full visibility in complex workflows.
- **Status**: Processed and cataloged (added as practical monitoring resource; useful for multi-agent evaluation)

### Entry 016: Claude Company Org Chart — 42+ Curated Skills Pack (Departments + Installable Skills)

- **URL**: https://x.com/i/status/2076221471375122811
- **Date**: 2026-07-12 (post)
- **Poster**: Charlie Hills (@charliejhills)
- **Summary / Key Claims**: Curated collection of 42+ installable skills for Claude, organized like a real company org chart (Developers, Designers, Marketing, Social Media, Finance, Small Business, Legal). Each department has specific skills with direct GitHub/install links (e.g., Superpowers, Context7, Skill Creator, UI UX Pro Max, Taste, Marketing skills pack, etc.). Every skill is real and installable. Turns Claude into a full "company" of specialized agents.
- **Extracted Repos / Tools**: Multiple linked repos including https://github.com/obra/superpowers, https://github.com/upstash/context7, and various skill packs (marketing, social, finance, legal, small business). Pattern: curated, installable SKILL.md-style packs organized by business function.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Skills & Prompt Engineering. High-signal curated skill library with org-chart structure.
- **Notes**: Excellent large-scale complement to gstack (Entry 010), Multica (Entry 012), and skills collections (Matt Pocock, marketing-council). Provides a broad "company departments" org structure on top of reusable skills. Strong overlap in the skills/reusable prompt pattern but at much larger scale (42+ skills across business functions). Low-to-medium redundancy risk — it's a curated, installable library rather than a new framework. High fit for evaluation criteria: Very High Relevance (broad skills across domains), High Integration (many direct install links), High Reproducibility (GitHub-based skills), Medium Redundancy (extends existing skills theme at scale). Perfect for the repo's reproduction goal — easy to document as a best-practice "AI company" skill library. Recommend: (1) Catalog as major skills resource. (2) Strong candidate for examples/ or bootstrap/ integration (many installable skills). (3) Synergistic with gstack/Multica for role-based + org-structured agent teams.
- **Status**: Processed and cataloged (added as major curated skills resource; high value for broad domain coverage)

### Entry 017: Graphify — Codebase Knowledge Graph for Agents (Tree-sitter Parsed, Queryable Graph)

- **URL**: https://x.com/i/status/2076092909372453048
- **Date**: 2026-07-11 (post)
- **Poster**: Tech with Mak (@techNmak)
- **Summary / Key Claims**: 82K-star repo that turns an entire project into a queryable knowledge graph (functions, classes, files, SQL schemas, infrastructure, docs, PDFs, images, videos as connected nodes). Agents traverse the graph instead of repeatedly grepping/opening files. Uses tree-sitter for local parsing (no embeddings, no vector DB, no LLM for graph itself). Calls, imports, inheritance become graph edges. Relationships marked EXTRACTED / INFERRED / AMBIGUOUS. Installs hooks/persistent instructions for Claude Code, Codex, Cursor, Gemini CLI, Copilot +20 agents. Graph committable to Git, auto-rebuilt after commits, team-shareable, MCP-exposed. Core idea: "Map once, query forever" instead of rereading the repo.
- **Extracted Repos / Tools**: Primary: Graphify (82K stars, implied GitHub repo in post). Code-to-graph tool with tree-sitter parsing and agent hooks.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Codebase Knowledge Graph & Memory. High-signal code-to-graph tool.
- **Notes**: **Potential first true duplicate / strong overlap with codebase-memory-mcp and repowise (Entry 006) context optimization**. Both aim to reduce wasteful file reads/greps by providing structured context to agents. Graphify uses explicit graph (tree-sitter parsed relationships) vs. repowise's smart retrieval layer or codebase-memory-mcp's graph memory. Similar "map once, query structured context" philosophy. Low-to-medium redundancy risk — Graphify adds explicit graph traversal + relationship confidence marking + broad non-code asset support (docs/PDFs/images/videos) + MCP exposure. High fit for evaluation criteria: Very High Relevance (codebase knowledge graph for agents), High Integration (hooks for 20+ agents, MCP), High Reproducibility (open source, Git-committable), Medium Redundancy (overlaps with existing graph/memory tools but adds explicit parsing + confidence labels). Recommend: (1) Catalog with explicit comparison to codebase-memory-mcp/repowise. (2) Evaluate for complementary use (Graphify for deep relationship queries; repowise for quick retrieval). (3) Strong candidate for reproduction notes on code-to-graph patterns.
- **Status**: Processed and cataloged (added with explicit duplicate/comparison analysis; high value for context/memory category)

### Entry 018: Getting Started with Loops — Autonomous Agent Loops Framework (4 Autonomy Tiers + 14-Step Roadmap)

- **URL**: https://x.com/i/status/2076283449388785847
- **Date**: 2026-07-12 (post)
- **Poster**: Annatar.md (@xieike)
- **Summary / Key Claims**: Detailed guide turning Claude into an autonomous "employee that ships while you sleep." Defines 4 loop types by autonomy level: Turn-based (25%, one task/round, control returns to you — best for unclear requirements); Goal-based (70%, define "done" with /goal + separate evaluator that keeps sending Claude back until tests/scores/bugs cleared); Time-based (60%, scheduled /loop e.g. check PR every 5 min, address reviews, fix CI); Proactive (95%, event fires, router dispatches child agents in parallel, review model oversees — no human online). Emphasizes that loop quality depends on system quality and tokens are the real cost. Includes 14-step roadmap from manual prompts to full loops using /goal, SKILL.md, worktrees, MCP, etc.
- **Extracted Repos / Tools**: No single new repo (framework/pattern doc). Key patterns: /goal + evaluator loops, time-based scheduled loops, proactive router + parallel child agents + review oversight, SKILL.md, worktrees, MCP integration. Strong alignment with autonomous agent system design.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Autonomous Loops & Agentic Workflows. High-signal practical framework for autonomous operation.
- **Notes**: Excellent complement to gstack (Entry 010), Multica (Entry 012), Jamon Holmgren setup (Entry 007), and harness engineering. Shares many elements: structured workflows, specialist behaviors, autonomous loops, self-healing/evaluation, SKILL.md, MCP, traces/reviews. Proactive tier (router + parallel child agents + review model) overlaps with Multica's issue assignment and gstack's role chaining. Goal-based + evaluator is a concrete implementation of self-healing docs and false-confidence audits from Jamon. Low redundancy — it's a practical "loops as autonomous employees" framework with specific autonomy tiers and a clear 14-step roadmap. High fit for evaluation criteria: Very High Relevance (autonomous loops + system design), High Integration (MCP, SKILL.md, worktrees), High Reproducibility (roadmap + specific patterns), Low Redundancy. Perfect for the repo's reproduction goal — easy to document as best-practice autonomous loop templates. Recommend: (1) Catalog as core autonomous workflows resource. (2) Strong candidate for reproduction scripts/templates in harness/ or examples/. (3) Synergistic with gstack/Multica for role-based + looped autonomous teams.
- **Status**: Processed and cataloged (added as major autonomous loops framework; high value for practical agentic system design)

### Entry 019: 7 Open Source Alternatives to Cursor/Perplexity/v0 (OpenHands, Zed, Codex, Scira, Morphic, December, Libra)

- **URL**: https://x.com/i/status/2076308228510765481
- **Date**: 2026-07-12 (post)
- **Poster**: Harman (@itsharmanjot)
- **Summary / Key Claims**: List of 7 open source repos that combine capabilities of Cursor, Perplexity, and v0 with zero waitlists, zero API markups, and zero vendor lock-in. Includes: OpenHands (agentic coding platform that plans, edits files, runs terminal commands, browses web autonomously — MIT); Zed (Rust-native AI editor, GPU-accelerated, open agent client protocol, 86k stars); Codex (OpenAI's official terminal coding agent in network-isolated containers, 94k stars, Apache 2.0); Scira (minimalist Perplexity alternative with citations and focus modes, 11.7k stars); Morphic (open source answer engine with generative UI streaming charts/comparisons, MIT); December (self-hosted v0/lovable alternative, $5 API credits for 50+ full app generations, Docker deploy); Libra (Cloudflare-native v0/Lovable alternative, serverless, free tier friendly, BYOK). Emphasizes closed source losing ground to open alternatives.
- **Extracted Repos / Tools**: OpenHands (MIT agentic coding platform); Zed (86k stars, open agent client protocol); Codex (94k stars, Apache 2.0, terminal coding agent in containers); Scira (11.7k stars, Perplexity alternative); Morphic (MIT answer engine with generative UI); December (self-hosted v0/lovable alternative); Libra (Cloudflare-native v0/Lovable alternative). Strong collection of open-source coding agents, editors, search/answer engines, and app generation tools.
- **TOOLS.md Link**: New rows under Agent Frameworks & Orchestration / Coding Agents (OpenHands, Zed, Codex) and Research/Search & Answer Engines (Scira, Morphic) and App Generation/UI Tools (December, Libra). High-signal open-source alternatives list.
- **Notes**: Excellent addition for reducing vendor lock-in and expanding open-source options in coding agents, AI editors, and app generation. OpenHands, Zed, and Codex have strong overlap with existing coding agent entries (Continue, Aider, ponytail, gstack, Multica, Spec Kit, Graphify, loops framework) — they are full agentic coding platforms or editors with agent protocols. Scira/Morphic add research/answer engine capabilities (less direct overlap, useful for context/research workflows). December/Libra add self-hosted v0/Lovable-style app generation (new but complementary to agentic coding). Low-to-medium redundancy overall — expands the open-source coding/agent ecosystem significantly. High fit for evaluation criteria: Very High Relevance (open-source alternatives to popular closed tools), High Integration (agent-compatible, Docker/self-hosted options), High Reproducibility (open source repos with clear licenses), Low Redundancy (broadens options without duplicating core frameworks). Perfect for the repo's open-source/self-hosted focus and reproduction goal. Recommend: (1) Catalog OpenHands, Zed, and Codex as core coding agent alternatives. (2) Add Scira/Morphic under research tools. (3) Note December/Libra as app generation complements. (4) Strong for local/self-hosted reproduction templates.
- **Status**: Processed and cataloged (added as major open-source alternatives resource; high value for expanding ecosystem options)

### Entry 020: Live Obsidian Business Network Graph (500+ Businesses, Real-Time ERP Sync)

- **URL**: https://x.com/i/status/2076341049480405440
- **Date**: 2026-07-12 (post)
- **Poster**: NO1ennn (@N01ennn)
- **Summary / Key Claims**: Real-world production example of a 34-year-old operator mapping 500+ businesses into one live Obsidian knowledge graph that updates in real time with every transaction from his internal ERP. Central node = operator; primary radials = business verticals; secondary connections = supplier/customer overlaps, shared employees, joint assets. Every business is a note; every deal/invoice/shared employee/joint asset creates or updates links. Graph auto-rewires on new data. Uses Obsidian's force-directed layout for real-time visualization. Primary use: identifying truly independent businesses vs. highly interdependent ones for merge/spin-off decisions. Contrasted with typical fragmented setup (multiple CRMs, spreadsheets, WhatsApp groups).
- **Extracted Repos / Tools**: No new standalone repo (production pattern using Obsidian + markdown + live ERP-to-vault sync). Pattern: live data pipeline from ERP → markdown notes in Obsidian vault → dynamic knowledge graph with force-directed visualization. Strong real-world validation of Obsidian as a scalable business intelligence / operations graph.
- **TOOLS.md Link**: New row under Personal Knowledge Management & Second Brain Workflows (or Business Intelligence / Operations Knowledge Graphs). High-signal real-world case study and pattern.
- **Notes**: **Excellent real-world complement and production-scale example of Entry 014 (Karpathy Second Brain / Obsidian + Claude Code Wiki)**. This is the enterprise/business-network version of the personal second brain concept — live data ingestion, dynamic linking, and visualization at massive scale (500+ entities). Strong overlap with **Graphify (Entry 017)** in the core idea of turning complex relational data into a queryable, visual knowledge graph (codebase vs. business network). Both emphasize "map once, query/visualize forever" with automatic updates. Low redundancy — this is a case study and pattern (live Obsidian + ERP sync) rather than a new tool or framework. High inspirational and reproduction value for anyone building knowledge graphs for operations, business intelligence, or complex networks. High fit for evaluation criteria: Very High Relevance (live knowledge graph at scale), High Reproducibility (Obsidian + markdown + ERP sync pattern is accessible), High Inspiration for local/self-hosted setups. Perfect for the repo's reproduction goal — document as best-practice example of Obsidian as a live business network graph. Recommend: (1) Catalog as major real-world case study. (2) Strong candidate for reproduction notes or templates showing ERP → Obsidian live sync patterns. (3) Synergistic with Entry 014 and Graphify for knowledge graph best practices across personal and business domains.
- **Status**: Processed and cataloged (added as major real-world knowledge graph case study; high value for scaling the second brain / graph pattern)

### Entry 021: Loop Engineering Guide 2026 — Structured Autonomous Agent Loops Framework

- **URL**: https://x.com/i/status/2076299893334016444 (and https://www.aibuilderclub.com/blog/loop-engineering-guide-2026)
- **Date**: 2026-07-12 (post)
- **Poster**: Roan (@RohOnChain)
- **Summary / Key Claims**: Points to a comprehensive free guide on "Loop Engineering" for AI agents — described as one of the best resources available. Covers structured approaches to building autonomous agent loops (including different autonomy models). Emphasizes that most AI engineers are unfamiliar with the term "loop engineering." Includes diagrams and practical setups. Strong focus on systematic, reliable agent loop design for production use.
- **Extracted Repos / Tools**: No new standalone repo (educational/practical guide). Key patterns: structured loop engineering with varying autonomy levels, systematic agent workflow design, likely covering goal-based, time-based, and proactive loops similar to other resources in the catalog.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Autonomous Loops & Agentic Workflows. High-signal dedicated guide on loop engineering.
- **Notes**: **Strong overlap with Entry 018 (Getting Started with Loops)** — both focus on structured autonomous agent loops with different autonomy tiers (turn-based, goal-based, time-based, proactive). This appears to be a more comprehensive or alternative guide to the same core concept of "loop engineering" for reliable agentic systems. Shares emphasis on system quality, evaluation, and moving beyond ad-hoc prompting. Low-to-medium redundancy — valuable to have multiple high-quality perspectives on this important topic. High fit for evaluation criteria: Very High Relevance (structured loop engineering for agents), High Reproducibility (dedicated free guide with practical setups), Low Redundancy when positioned as complementary resource. Perfect for the repo's reproduction goal — another strong source for autonomous loop best practices and templates. Recommend: (1) Catalog as major loop engineering resource. (2) Explicitly compare/contrast with Entry 018 (different models or depth of coverage). (3) Strong candidate for reproduction templates combining ideas from both guides. (4) Synergistic with gstack, Multica, and harness engineering entries for structured autonomous workflows.
- **Status**: Processed and cataloged (added as major loop engineering resource; explicit comparison to Entry 018 noted)

## Future Entries Format

When adding new X-sourced tools or papers:

```
### Entry NNN: Short Title

- **URL**: https://x.com/...
- **Date**: YYYY-MM-DD
- **Poster**: @handle (Name)
- **Summary**: 1-2 sentence gist + why relevant to local LLM dev pipelines. Note if paper-based.
- **Extracted Repos/Tools**: List with links or 'Paper only: arxiv link'.
- **TOOLS.md Link**: Row or section reference.
- **Notes**: Any caveats, hype vs substance, feasibility if paper, pipeline fit.
```

*This log ensures the catalog remains grounded in primary social signals while allowing rigorous, staged evaluation separate from viral claims. 'Read a paper' is now a supported recurring workflow for tool discovery.*