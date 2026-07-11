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

## Current Status (v0.3 - Grok CLI bootstrap + methodology)

- Repo created with comprehensive structure.
- Categorization taxonomy and staged ranking rubric defined (CATEGORIZATION.md).
- Placeholder for first seed X post still pending content extraction.
- **v0.2**: Selective git subtree / submodule / pinned-SHA tracking (SUBTREES.md) + aggregates intake.
- **New in v0.3**: Replayable **Grok CLI bootstrap** under `bootstrap/grok-cli/` — first real integration artifact. Packages portable skills (`adr`, `docs`, `open-questions`, `karpathy-guidelines`), ponytail skill snapshot, MCP `codebase-memory` wiring, and an idempotent `install.sh` for new environments.
- Seeded tools in TOOLS.md / data/tools.json include bootstrap stack components + prior demo entries.

**Next immediate steps**:
1. Provide content/summary from https://x.com/i/status/2075994424484732984 → full categorization + scoring pass.
2. Add first real aggregate or individual tool using SUBTREES.md / sources/aggregates.md workflows.
3. Prototype evaluation harness (LiteLLM + DSPy + MCP memory) on top of the bootstrap environment.
4. Optionally add first selective subtree/submodule once a qualifying high-value tool is identified.

## Grok CLI bootstrap (new machine)

```bash
# After installing Grok: curl -fsSL https://x.ai/cli/install.sh | bash
git clone git@github.com:themark-net/local-llm-dev-tools.git
cd local-llm-dev-tools
./bootstrap/grok-cli/install.sh --with-codebase-memory
grok login   # or export XAI_API_KEY=...
```

Details, flags, and refresh workflow: [bootstrap/grok-cli/README.md](bootstrap/grok-cli/README.md).

## Repository Structure

```
local-llm-dev-tools/
├── README.md
├── CATEGORIZATION.md          # Taxonomy + staged 0-100 rubric + refinement process
├── SUBTREES.md                # Selective subtree/submodule/pinned-SHA policy + workflows
├── TOOLS.md                   # Master scored table + integration notes (Grok CLI, MCP, DSPy)
├── sources/
│   ├── x-posts.md             # Log of X seed posts
│   └── aggregates.md          # Aggregate/list repos intake + synthesis
├── data/
│   └── tools.json             # Structured catalog (pins, bootstrap paths, scores)
├── bootstrap/
│   └── grok-cli/              # Replayable Grok skills + MCP + config install
│       ├── install.sh
│       ├── manifest.json
│       ├── skills/            # adr, docs, open-questions, karpathy-guidelines
│       └── skills-external/   # ponytail snapshot (skills.paths)
├── examples/
│   └── integration-patterns/  # Future: scripts, compose files, GitHub Actions
├── pipelines/                 # Future: continuous eval & deploy harnesses
└── .github/                   # Future: issue/PR templates
```

## Categorization Taxonomy & Ranking (Summary)

See CATEGORIZATION.md for full details. Tools receive primary category + tags, then Stage 0 gate + weighted Stages 1-4 (Core LLM/Agent Compatibility 35%, Perf/Efficiency 25%, Pipeline Integration 25%, Ecosystem 15%). Overall 0-100 score → S/A/B/C tiers. Explicit focus on Grok CLI compatibility, tool calling, MCP code memory hooks, and pipeline extensibility.

## Selective Copy Strategy (New v0.2)

Most tools use **pinned commit + shallow clone** in pipelines (recorded in data/tools.json). 

Rare high-value, small, heavily customized tools may use `git subtree` under `tools/<name>/` (see SUBTREES.md for strict criteria and commands).

Aggregate/list repos (awesome-lists, comparison tables) are logged in sources/aggregates.md, assigned a handling tier (A=submodule/subtree, B=pin+archive, C=extract only), and synthesized into the central TOOLS.md / data/tools.json using the rubric. This keeps one authoritative, scored catalog while still preserving source context.

## Initial Seeded Tools

See TOOLS.md for full details.

| Tool | Primary Category | Overall | Tier | Tracking Method |
|------|------------------|---------|------|-----------------|
| **Grok CLI bootstrap** | Pipeline & CI/CD | 94 | S | first-party under `bootstrap/grok-cli/` |
| codebase-memory-mcp | Memory & RAG | 91 | S | pinned upstream + optional binary install |
| LiteLLM | Proxy & Routing | 93 | S | pinned_commit + shallow clone |
| Ollama | Inference & Serving | 92 | S | pinned_commit + shallow clone |
| Continue.dev | Coding & Dev Agents | 90 | S | pinned_commit + shallow clone |
| ponytail (skills) | Coding & Dev Agents | 86 | A | skills snapshot in bootstrap |
| Aider | Coding & Dev Agents | 87 | A | pinned_commit + shallow clone |
| DSPy | Agent Frameworks | 85 | A | pinned_commit + shallow clone |
| karpathy-guidelines | Coding & Dev Agents | 84 | A | vendored skill (MIT) |

**Placeholder for Seed X Post**: Awaiting content. Will be processed via sources/x-posts.md → rubric scoring → appropriate tracking method (pinned / subtree / aggregate synthesis).

## How to Contribute / Add New Items

- Individual tool or X post: Open Issue or PR updating TOOLS.md + data/tools.json + sources/x-posts.md. Apply rubric.
- Aggregate/list repo: Use sources/aggregates.md template. Decide tier, synthesize into central catalog.
- Subtree/submodule request: Must meet strict criteria in SUBTREES.md. Provide rationale tied to pipeline value.

All additions should improve the Grok CLI + MCP + pipeline vision or fill a clear gap in the scored catalog.

---

* v0.3 Grok CLI bootstrap added 2026-07-11. Methodology from v0.2 remains the catalog backbone.*