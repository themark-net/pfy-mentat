# local-llm-dev-tools

**Track • Categorize • Rank • Integrate** local LLM development tools, agents, frameworks, and infrastructure for building robust, self-hosted continuous pipelines.

Seeded from X (Twitter) posts and community sources. Designed for iterative evaluation and integration with Grok CLI, custom agents, MCP-style code memory systems, LiteLLM routing, and production DevOps workflows.

Repository: https://github.com/themark-net/local-llm-dev-tools

## Goals

- Maintain a living, versioned catalog of the best local-first LLM tools.
- Apply consistent, multi-stage evaluation criteria for compatibility, performance, agentic capability, and pipeline readiness.
- Identify synergies for a unified local development stack (inference + agents + memory + orchestration + CI/CD).
- Enable rapid prototyping and deployment of custom pipelines using the highest-ranked components.
- Support Grok CLI as primary interface initially, with fallback/hybrid to other identified toolsets based on task requirements.
- Provide selective, reproducible copies of critical tools via subtree/submodule or pinned commits while keeping the tracking repo lean.

## Current Status (v0.2 - Methodology & Tracking Infrastructure)

- Repo created with comprehensive structure.
- Categorization taxonomy and staged ranking rubric defined (CATEGORIZATION.md).
- Placeholder for first seed X post still pending content extraction.
- **New in v0.2**: Full methodology for selective git subtree / submodule / pinned-SHA tracking of individual tools (SUBTREES.md) and handling of aggregate/list repos (sources/aggregates.md + extended data/tools.json).
- Seeded demonstration tools in TOOLS.md and data/tools.json using default pinned-commit approach (no bloat from large repos).
- No pipelines or integration code yet; catalog + methodology complete and ready for first real X seed or aggregate.

**Next immediate steps**:
1. Provide content/summary from https://x.com/i/status/2075994424484732984 → full categorization + scoring pass (individual tool or aggregate).
2. Add first real aggregate or individual tool using the new SUBTREES.md / sources/aggregates.md workflows.
3. Prototype evaluation harness or example integration (LiteLLM + DSPy + MCP memory).
4. Optionally add first selective subtree/submodule once a qualifying high-value tool is identified.

## Repository Structure

```
local-llm-dev-tools/
├── README.md
├── CATEGORIZATION.md          # Taxonomy + staged 0-100 rubric + refinement process
├── SUBTREES.md                # NEW: Selective subtree/submodule/pinned-SHA policy + exact workflows
├── TOOLS.md                   # Master scored table + integration notes (Grok CLI, MCP, DSPy)
├── sources/
│   ├── x-posts.md             # Log of X seed posts (first one pending)
│   └── aggregates.md          # NEW: Log + intake template for aggregate/list repos + synthesis process
├── data/
│   └── tools.json             # v0.2 extended schema with pinned_commit, subtree_path, source_aggregate, aggregates array
├── examples/
│   └── integration-patterns/  # Future: scripts, compose files, GitHub Actions
├── pipelines/                 # Future: continuous eval & deploy harnesses
└── .github/                   # Future: issue/PR templates for new tool/aggregate submissions
```

## Categorization Taxonomy & Ranking (Summary)

See CATEGORIZATION.md for full details. Tools receive primary category + tags, then Stage 0 gate + weighted Stages 1-4 (Core LLM/Agent Compatibility 35%, Perf/Efficiency 25%, Pipeline Integration 25%, Ecosystem 15%). Overall 0-100 score → S/A/B/C tiers. Explicit focus on Grok CLI compatibility, tool calling, MCP code memory hooks, and pipeline extensibility.

## Selective Copy Strategy (New v0.2)

Most tools use **pinned commit + shallow clone** in pipelines (recorded in data/tools.json). 

Rare high-value, small, heavily customized tools may use `git subtree` under `tools/<name>/` (see SUBTREES.md for strict criteria and commands).

Aggregate/list repos (awesome-lists, comparison tables) are logged in sources/aggregates.md, assigned a handling tier (A=submodule/subtree, B=pin+archive, C=extract only), and synthesized into the central TOOLS.md / data/tools.json using the rubric. This keeps one authoritative, scored catalog while still preserving source context.

## Initial Seeded Tools (Demonstration)

See TOOLS.md for full details. All currently use the default pinned-commit approach.

| Tool | Primary Category | Overall Score | Tier | Tracking Method |
|------|------------------|---------------|------|-----------------|
| LiteLLM | Proxy & Routing | 93 | S | pinned_commit + shallow clone |
| Ollama | Inference & Serving | 92 | S | pinned_commit + shallow clone |
| Continue.dev | Coding & Dev Agents | 90 | S | pinned_commit + shallow clone |
| Aider | Coding & Dev Agents | 87 | A | pinned_commit + shallow clone |
| DSPy | Agent Frameworks | 85 | A | pinned_commit + shallow clone |

**Placeholder for Seed X Post**: Awaiting content. Will be processed via sources/x-posts.md → rubric scoring → appropriate tracking method (pinned / subtree / aggregate synthesis).

## How to Contribute / Add New Items

- Individual tool or X post: Open Issue or PR updating TOOLS.md + data/tools.json + sources/x-posts.md. Apply rubric.
- Aggregate/list repo: Use sources/aggregates.md template. Decide tier, synthesize into central catalog.
- Subtree/submodule request: Must meet strict criteria in SUBTREES.md. Provide rationale tied to pipeline value.

All additions should improve the Grok CLI + MCP + pipeline vision or fill a clear gap in the scored catalog.

---

* v0.2 methodology implemented 2026-07-11. Ready for first real seed data.*