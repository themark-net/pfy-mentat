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
- **TOOLS.md Link**: Added under Agent Frameworks & Orchestration / Multi-Agent Skills & Workflows. Strong fit as a comprehensive, battle-tested example of role-specialized agent skills and chained workflows.
- **Notes**: Outstanding high-signal addition. Directly complements and extends several recent entries: multi-expert council patterns (marketing-council), composable skills (Matt Pocock), structured agentic setups and reviews (Jamon Holmgren), context/prompt efficiency (Ruben Hassid hacks), and harness engineering principles. The role specialization + workflow chaining is a powerful template for local Grok CLI skills or DSPy modules. Patterns like specialist personas, guardrails, memory, and cross-review are highly portable beyond Claude. Recommend: (1) Catalog as core reference for multi-agent orchestration. (2) Explore porting/adapting key skills or the overall structure into bootstrap/grok-cli/skills/ or examples/. (3) Note in AGENTS.md as inspiration for router + specialist behaviors. Massive community validation via stars and forks.
- **Status**: Processed and cataloged (added as major workflow/multi-skill resource; strong recommendation for integration experiments)

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