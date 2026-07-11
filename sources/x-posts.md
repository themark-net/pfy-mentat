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