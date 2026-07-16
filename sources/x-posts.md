### Entry 054: OpenClaude-Portable — Folder-Based Portable Coding Agent (Multi-Provider, No Install)

- **URL**: https://x.com/i/status/2077768643128009110
- **Date**: 2026-07-16
- **Poster**: Tom Dörr (@tom_doerr)
- **Summary / Key Claims**: OpenClaude-Portable is a fully portable coding agent that runs directly from a folder with no installation required on Windows, Linux, or macOS. It aggregates Anthropic (Claude), OpenAI, Google Gemini, and Ollama into a unified web dashboard with agent capabilities. Designed for easy use on temporary or shared machines.
- **Extracted Repos / Tools**: Primary: https://github.com/techjarves/OpenClaude-Portable — Portable, folder-based multi-provider coding agent.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration / Portable & Lightweight Agents (strong fit for new lightweight harness direction).
- **Notes**: **Very high relevance to current pivot.** This directly supports the shift to a lightweight, scriptable, local-first harness (OpenCode + Grok build CLI). The "run from folder, no install" model is ideal for portable, reproducible environments. Strong candidate to evaluate as a core runtime or reference implementation for the harness. Complements our focus on OpenCode and custom agent CLIs. High fit for evaluation criteria: Very High Relevance (portable lightweight agent), High Integration Ease (folder-based, multi-provider), High Reproducibility (open source), Low Redundancy. Recommend: (1) Catalog as top portable agent option. (2) Strong candidate for direct testing/integration into `bootstrap/setup-lightweight-harness.py`. (3) Evaluate as potential primary runtime or unified dashboard layer alongside OpenCode and Grok CLI.
- **Status**: Processed and cataloged (added as high-value portable lightweight agent; priority for harness integration)

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