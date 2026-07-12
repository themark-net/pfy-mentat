# local-llm-dev-tools

**Track • Categorize • Rank • Integrate** local LLM development tools, agents, frameworks, and infrastructure for building robust, self-hosted continuous pipelines.

Seeded from X (Twitter) posts and community sources. Designed for iterative evaluation and integration with **Grok CLI**, custom agents, **MCP** code memory, LiteLLM routing, containerized harnesses, and production DevOps workflows.

Repository: https://github.com/themark-net/local-llm-dev-tools

## Goals

- Maintain a living, versioned catalog of the best local-first LLM tools.
- Apply consistent, multi-stage evaluation criteria for compatibility, performance, agentic capability, and pipeline readiness.
- Identify synergies for a unified local development stack (inference + agents + memory + orchestration + CI/CD).
- Enable rapid prototyping and deployment of custom pipelines using the highest-ranked components.
- Support Grok CLI as primary interface initially, with fallback/hybrid to other identified toolsets based on task requirements.
- Provide selective, reproducible copies of critical tools via pinned commits (rare subtree) while keeping the tracking repo lean.
- Test integrations in **versioned container sandboxes** (agent-cage) so host systems stay clean and results are reproducible.

## Process docs (agents & humans)

| Artifact | Path | Role |
|----------|------|------|
| **Design** | [docs/DESIGN.md](docs/DESIGN.md) | Master goals, system shape, non-goals |
| **Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Short structural snapshot |
| **ADR** | [docs/adr/](docs/adr/README.md) | Settled decisions + **rejected alternatives** |
| **TODO** | [docs/TODO.md](docs/TODO.md) | Ordered next steps (links to OQs) |
| **Open questions** | [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | TBDs; detail may live next to work citing `OQ-NNNN` |
| **Agent entry** | [AGENTS.md](AGENTS.md) | Mandatory read list + do-nots |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) | How to add seeds/tools |
| **Catalog docs skill** | `/catalog-docs` | Keep README, triple-write catalog, harness docs consistent |

When architecture pivots: `/adr`. When something is unsettled: `/open-questions`. When documenting this repo: **`/catalog-docs`**. Work queue: `docs/TODO.md`.

## Skills (Grok)

After `./bootstrap/grok-cli/install.sh`, these are available:

| Skill | Slash | Purpose |
|-------|-------|---------|
| **catalog-docs** | `/catalog-docs` | **This repo’s** documentation skill (README, TOOLS/json/x-posts triple-write, harness, audit) |
| docs | `/docs` | Portable module/ops docs for any project |
| adr | `/adr` | Architecture decisions + rejected alternatives |
| open-questions | `/open-questions` | TBD parking lot |
| project-process | `/project-process` | Scaffold DESIGN/ADR/TODO/OQ into a new repo |
| karpathy-guidelines | (auto) | Anti-overcomplication defaults |
| ponytail | (via skills path) | Minimalism / YAGNI modes |

Project skill source of truth: [`.grok/skills/catalog-docs/`](.grok/skills/catalog-docs/) (also vendored under `bootstrap/grok-cli/skills/catalog-docs/` for reinstall).

**Catalog triple-write rule:** every processed tool seed must update `sources/x-posts.md` (if social/paper) **and** `TOOLS.md` **and** `data/tools.json` (JSON must parse). `/catalog-docs seed` or `/catalog-docs audit` enforces this.

## Current Status (v0.4)

- Methodology: taxonomy, rubric, SUBTREES, aggregates intake.
- Process layout: DESIGN + multi-file ADR + TODO + open questions (ADR-0001).
- **Grok CLI bootstrap** + **project-process** scaffold (replayable operator + new-project process).
- **Phase 0 catalog sync:** mobile X seeds Entries 001–010 + structured `data/tools.json` (18 tools); see [TOOLS.md](TOOLS.md).
- **agent-cage (PNNL)** as primary **container integration lab** under [`harness/agent-cage/`](harness/agent-cage/) (Make + pin + MCP).
- **`/catalog-docs`** skill for repository documentation consistency.

**Next steps** (authoritative: [docs/TODO.md](docs/TODO.md)):

1. Cage smokes + first tool integrations (LiteLLM, MCP, repowise) — T-0021  
2. Skill ports (mattpocock / marketing-council / gstack patterns) — T-0011  
3. Eval harness prototype — T-0003 / [OQ-0002](docs/open-questions/OQ-0002-eval-harness-shape.md)  
4. Optional colibri / Antigravity — hardware/use-case gated  

Plans: [docs/ops/plan-mobile-seed-integration.md](docs/ops/plan-mobile-seed-integration.md), [docs/ops/harness-integration-framework.md](docs/ops/harness-integration-framework.md).

## Bootstrap (new machine + new projects)

### Operator environment (Grok skills + MCP)

```bash
# After installing Grok: curl -fsSL https://x.ai/cli/install.sh | bash
git clone git@github.com:themark-net/local-llm-dev-tools.git
cd local-llm-dev-tools
./bootstrap/grok-cli/install.sh --with-codebase-memory
grok login   # or export XAI_API_KEY=...
```

Installs skills: `adr`, `docs`, `open-questions`, `karpathy-guidelines`, `project-process`, **`catalog-docs`**, plus ponytail path + codebase-memory MCP wiring.  
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
Details: [bootstrap/project-process/README.md](bootstrap/project-process/README.md).

### Container harness (integration lab)

```bash
cd harness/agent-cage
make doctor && make setup && make up-mcp   # sandbox + MCP overlay
make shell                                 # Ubuntu agent
make test                                  # policy smoke
make down
```

Upstream: [pnnl/agent-cage](https://github.com/pnnl/agent-cage) (pinned SHA in `harness/agent-cage/PINNED_COMMIT`).  
Use the cage to version **images** and test catalog tools in isolation (LiteLLM, repowise, skill installs, etc.).  
Details: [harness/agent-cage/README.md](harness/agent-cage/README.md).

## Repository Structure

```
local-llm-dev-tools/
├── README.md
├── AGENTS.md                  # Agent entry: mandatory reads + workflow practices
├── CONTRIBUTING.md            # Seed/tool contribution guidelines
├── CATEGORIZATION.md          # Taxonomy + staged 0-100 rubric
├── SUBTREES.md                # Selective subtree/submodule/pinned-SHA policy
├── TOOLS.md                   # Master scored table + integration notes
├── .grok/skills/
│   └── catalog-docs/          # Project skill: document this repository
├── docs/
│   ├── DESIGN.md              # Master design (goals + shape)
│   ├── ARCHITECTURE.md        # Structural snapshot
│   ├── TODO.md                # Central next steps → OQ links
│   ├── OPEN_QUESTIONS.md      # Central TBD index
│   ├── adr/                   # ADRs (decisions + rejected paths)
│   ├── open-questions/        # OQ detail files
│   ├── ops/                   # Plans + harness framework
│   └── automation/            # Standing monitors (e.g. tom-doer)
├── sources/
│   ├── x-posts.md             # X/social seed log (Entries 001+)
│   └── aggregates.md
├── data/
│   └── tools.json             # Structured catalog (must stay valid JSON)
├── bootstrap/
│   ├── grok-cli/              # Operator env: skills + MCP + config
│   └── project-process/       # Scaffold process into any repo
├── harness/
│   └── agent-cage/            # Container sandbox (PNNL) + Makefile lab
├── examples/                  # Future integration patterns / smokes
└── pipelines/                 # Future continuous eval & deploy
```

## Catalog & scoring (summary)

See [CATEGORIZATION.md](CATEGORIZATION.md) and [TOOLS.md](TOOLS.md). Tools get Stage 0 gate + weighted Stages 1–4 → overall 0–100 → S/A/B/C tiers. Focus: Grok CLI, tool calling, MCP memory, pipeline extensibility.

**Default tracking:** pinned commit + shallow clone (`data/tools.json`). Rare subtree only if [SUBTREES.md](SUBTREES.md) criteria are met.

### Highlighted tools

| Tool | Overall | Tier | Tracking |
|------|---------|------|----------|
| Grok CLI bootstrap | 94 | S | `bootstrap/grok-cli/` |
| project-process bootstrap | 92 | S | `bootstrap/project-process/` |
| **agent-cage (PNNL)** | 90 | S | pin + `harness/agent-cage/` |
| codebase-memory-mcp | 91 | S | pin + bootstrap MCP |
| LiteLLM / Ollama | 93 / 92 | S | pinned_commit |
| repowise / gstack / mattpocock / marketing-skills | 85–88 | A | pin / skill snapshots |
| colibri | 86 | A | pin (weights not in-repo) |

Full table: [TOOLS.md](TOOLS.md). Seeds: [sources/x-posts.md](sources/x-posts.md).

## How to contribute

1. Read [CONTRIBUTING.md](CONTRIBUTING.md).
2. New X/tool: apply rubric → **triple-write** x-posts + TOOLS.md + tools.json (or run `/catalog-docs seed`).
3. Integration experiment: prefer `harness/agent-cage` for isolation; record notes in TOOLS.md.
4. Architecture pivot: `/adr`. Unsettled: `/open-questions`. Docs drift: `/catalog-docs audit`.

All additions should improve the Grok CLI + MCP + pipeline vision or fill a clear gap in the scored catalog.

---

*v0.4 — Phase 0 catalog sync, agent-cage harness, `/catalog-docs` skill. Process backbone from v0.3 (DESIGN/ADR/TODO/OQ).*
