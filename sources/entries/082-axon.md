### Entry 082: Axon — Graph-powered codebase intelligence (knowledge graph + MCP tools for agents)

- **URL**: https://x.com/i/status/2088089992698433808
- **Date**: 2026-08-14
- **Poster**: Tom Dörr (@tom_doerr)
- **Summary / Key Claims**: Indexes any codebase into a structural knowledge graph enabling visual exploration and AI agent querying through MCP tools. 12-phase pipeline (parse, call tracing, types, communities, execution flows, etc.); hybrid search; impact analysis; dead-code detection; watch mode.
- **Extracted Repos / Tools**: https://github.com/harshkedia177/axon (MIT, ~720–730★, Python + TypeScript; `pip install axoniq` / `uv add axoniq`; CLI: `axon analyze .` → `axon ui` / `axon serve --watch` for MCP)
- **TOOLS.md Link**: Proposed under Context & Memory / Codebase Knowledge Graph & MCP (initial scores: S1=90 S2=82 S3=92 S4=85 overall ~88 tier A). Tracking: proposed pin to latest PyPI or main.
- **Notes**: Stage 0 gate **PASS** (MIT; pip/uv one-liner; fully local zero-cloud; clear analyze → UI / MCP serve quickstart). Excellent fit — direct complement/competitor to Graphify, codebase-memory-mcp, Understand-Anything, repowise. Strengths: KuzuDB graph + Cypher, MCP tools (`axon_query`, `axon_context`, `axon_impact`, `axon_dead_code`), hybrid BM25+vector+fuzzy search, impact/dead-code/execution-flow analysis, live watch mode. Languages currently focused on Python/TS/JS. No commercial lock-in. Recommend: (1) catalog as A-tier code intelligence / MCP layer; (2) smoke-test `axon analyze` + MCP serve against a medium local repo and wire into Grok CLI / OpenCode; (3) optional deeper eval vs Graphify on token efficiency / agent accuracy. High pipeline value for reducing wasteful file reads and giving agents structural context.
- **Status**: Quick-evaluated - cataloged (initial scores)
