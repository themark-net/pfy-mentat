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