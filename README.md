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

## Process docs (agents & humans)

| Artifact | Path | Role |
|----------|------|------|
| **Design** | [docs/DESIGN.md](docs/DESIGN.md) | Master goals, system shape, non-goals |
| **Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Short structural snapshot |
| **ADR** | [docs/adr/](docs/adr/README.md) | Settled decisions + **rejected alternatives** |
| **TODO** | [docs/TODO.md](docs/TODO.md) | Ordered next steps (links to OQs) |
| **Open questions** | [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | TBDs; detail may live next to work citing `OQ-NNNN` |
| **Agent entry** | [AGENTS.md](AGENTS.md) | Mandatory read list + do-nots |

When architecture pivots: `/adr`. When something is unsettled: `/open-questions`. Work queue: `docs/TODO.md`.

## Current Status (v0.3 - Grok CLI bootstrap + methodology)

- Repo created with comprehensive structure.
- Categorization taxonomy and staged ranking rubric defined (CATEGORIZATION.md).
- Placeholder for first seed X post still pending content extraction ([OQ-0001](docs/open-questions/OQ-0001-seed-x-post-content.md)).
- **v0.2**: Selective git subtree / submodule / pinned-SHA tracking (SUBTREES.md) + aggregates intake.
- **v0.3**: Replayable **Grok CLI bootstrap** under `bootstrap/grok-cli/`.
- **Process layout**: DESIGN + multi-file ADR + TODO + open questions (ADR-0001).
- Seeded tools in TOOLS.md / data/tools.json include bootstrap stack components + prior demo entries.

**Next immediate steps** (authoritative list: [docs/TODO.md](docs/TODO.md)):
1. Seed X post intake — [T-0001](docs/TODO.md) / [OQ-0001](docs/open-questions/OQ-0001-seed-x-post-content.md)
2. First real aggregate or high-value tool — T-0002
3. Evaluation harness prototype — T-0003 / [OQ-0002](docs/open-questions/OQ-0002-eval-harness-shape.md)
4. Optional first subtree only if criteria met — T-0005 / [OQ-0003](docs/open-questions/OQ-0003-first-subtree-candidate.md)

## Bootstrap (new machine + new projects)

### Operator environment (Grok skills + MCP)

```bash
# After installing Grok: curl -fsSL https://x.ai/cli/install.sh | bash
git clone git@github.com:themark-net/local-llm-dev-tools.git
cd local-llm-dev-tools
./bootstrap/grok-cli/install.sh --with-codebase-memory
grok login   # or export XAI_API_KEY=...
```

Installs skills: `adr`, `docs`, `open-questions`, `karpathy-guidelines`, **`project-process`**, plus ponytail path + codebase-memory MCP wiring.  
Details: [bootstrap/grok-cli/README.md](bootstrap/grok-cli/README.md).

### New project process scaffold (DESIGN / ADR / TODO / OQ)

```bash
mkdir -p ~/work/my-app && cd ~/work/my-app && git init
/path/to/local-llm-dev-tools/bootstrap/project-process/init.sh . \
  --name my-app \
  --vision "One-line product vision" \
  --install-skills
```

Or in Grok: `/project-process init .`  
Details + evaluation vs heavier tools: [bootstrap/project-process/README.md](bootstrap/project-process/README.md).

## Repository Structure

```
local-llm-dev-tools/
├── README.md
├── AGENTS.md                  # Agent entry: mandatory reads + process rules
├── CATEGORIZATION.md          # Taxonomy + staged 0-100 rubric
├── SUBTREES.md                # Selective subtree/submodule/pinned-SHA policy
├── TOOLS.md                   # Master scored table + integration notes
├── docs/
│   ├── DESIGN.md              # Master design (goals + shape)
│   ├── ARCHITECTURE.md        # Structural snapshot
│   ├── TODO.md                # Central next steps → OQ links
│   ├── OPEN_QUESTIONS.md      # Central TBD index
│   ├── adr/                   # ADRs (decisions + rejected paths)
│   └── open-questions/        # OQ detail files
├── sources/
│   ├── x-posts.md
│   └── aggregates.md
├── data/
│   └── tools.json
├── bootstrap/
│   ├── grok-cli/              # Operator env: skills + MCP + config
│   └── project-process/       # Per-repo DESIGN/ADR/TODO/OQ scaffold + skill
├── examples/                  # Future integration patterns
└── pipelines/                 # Future eval & deploy harnesses
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
| **project-process bootstrap** | Pipeline & CI/CD | 92 | S | first-party under `bootstrap/project-process/` |
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

Architecture pivots: update [docs/adr/](docs/adr/README.md). Unsettled work: [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) + [docs/TODO.md](docs/TODO.md).

---

* v0.3 Grok CLI bootstrap + process docs (DESIGN/ADR/TODO/OQ) 2026-07-11. Methodology from v0.2 remains the catalog backbone.*