# AGENTS.md — pfy-mentat

Instructions for coding agents working in this repository.

## Mandatory reads (before non-trivial design or multi-step work)

1. [docs/DESIGN.md](docs/DESIGN.md) — goals, shape, non-goals, process model  
2. [docs/adr/README.md](docs/adr/README.md) — decision index (open full ADRs that touch your area)  
3. [docs/TODO.md](docs/TODO.md) — next steps  
4. [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) — do not silently “solve” P0/P1 OQs  

Also use as needed: `CATEGORIZATION.md`, `SUBTREES.md`, `TOOLS.md`, `bootstrap/grok-cli/README.md`.

## Process rules

| Situation | Action |
|-----------|--------|
| Architecture pivot / hard-to-reverse choice | Write **ADR** under `docs/adr/` with **rejected alternatives** (`/adr`) |
| Uncertain / can wait / needs human | **Open question** in central index; optional detail file or in-context note citing `OQ-NNNN` (`/open-questions`) |
| Implementation work item | Update **TODO** row; link OQs when blocked |
| Non-trivial module or bootstrap change | Operator + agent docs (`/docs`) |
| New catalog tool | Score with rubric; update TOOLS.md + data/tools.json + sources log |

## Do not

- Re-propose designs rejected in ADRs without a superseding ADR and new context  
- Leave P0–P2 questions only in chat  
- Embed large upstream repos without meeting `SUBTREES.md` (see ADR-0003)  
- Commit secrets, API keys, or `auth.json`  
- Create a second decision log outside `docs/adr/`  

## Bootstrap environment

```bash
./bootstrap/grok-cli/install.sh
# optional: --with-codebase-memory
```

Portable skills: `adr`, `docs`, `open-questions`, `karpathy-guidelines`, `project-process`, `one-shot`, `marketing-council`, **`investigate`** (RCA); ponytail + mattpocock subset (via `skills.paths`).  
**This repo:** `/catalog-docs` — document the catalog (README, triple-write, harness); source `.grok/skills/catalog-docs/`.

### Role router (gstack patterns, docs-first — T-0014)

Map **Think → Plan → Build → Review → Test → Ship → Reflect** without installing gstack:

| Stage / role | Prefer |
|--------------|--------|
| Product rethink (CEO) | Scope challenge → `/adr` or `/open-questions` |
| Plan / eng manager | mattpocock **`to-spec`** (paths) + DoD list |
| Build | Coding agent + karpathy / ponytail; **`/one-shot`** if DoD + lab ready |
| Debug / RCA | **`/investigate`** — Iron Law: no fix without root-cause hypothesis (T-0017) |
| Review | mattpocock **`code-review`** (paths); optional second persona |
| QA | `make cage-test`, `make smoke-*` (see [docs/modules/examples-smokes.md](docs/modules/examples-smokes.md)) |
| Security | write-guard + cage policy; not full gstack `/cso` |
| Ship | Feature branch → green checks → merge; [DEPLOY.md](docs/ops/DEPLOY.md) |
| Reflect | Update TODO/OQ; `/docs` or `/catalog-docs` if modules changed |
| Marketing multi-view | **`/marketing-council`** |

Full recipes and non-goals: **[docs/ops/gstack-role-recipes.md](docs/ops/gstack-role-recipes.md)**.  
Deeper-port scores (why not raw gstack install): **[docs/ops/gstack-skill-port-comparison.md](docs/ops/gstack-skill-port-comparison.md)**.  
Do **not** clone garrytan/gstack into this repo (ADR-0009).

### Scaffold process into another repo

```bash
./bootstrap/project-process/init.sh /path/to/repo --name <name> --vision "..."
# or: /project-process init <path>
```

## Advanced Agentic Workflows & Harness Practices (enhanced guidance)

This repo supports robust, production-like agentic coding setups inspired by high-signal workflows (e.g., comprehensive agentic checklists and harness engineering principles). Use these to make interactions more reliable, observable, and self-improving.

### AGENTS.md as Router & Onboarding
- Treat this file as the primary **router**: It directs agents to the right skills, docs, tools, and processes based on task type (research, planning, implementation, review, autonomous work).
- Include or reference summaries of key docs for quick greppability (first 7 lines of important files should be self-descriptive).
- Agents should use this to discover and load context dynamically.

### Self-Healing & Living Documentation
- Agents are encouraged (and instructed via skills/docs) to keep relevant docs updated as part of their work ("self-healing docs").
- For every system or module, maintain up-to-date docs; tag or let agents discover them via AGENTS.md.
- Commit updates with the work.

### Traces, Worksheets & Session Continuity
- For non-trivial or multi-session tasks, create or update **agent traces/worksheets** that record actions, decisions, blockers, and progress.
- Commit these with the work (use git tags for easy reference, e.g., corresponding to worksheet names).
- This enables handoff: another agent (or future session) can pick up exactly where left off.
- Reference in open-questions or TODOs as needed.

### Cross-Agent Reviews & Personas
- At major milestones (research, plan, implementation, wrap-up), perform cross-agent reviews using different models or personas where possible.
- Personas/examples: maintainability expert, security reviewer, performance analyst, "AI smells" detector, domain specialist.
- Document review criteria in dedicated docs or skills; agents should own/update related system docs.

### Custom Scripts, Tools & Automation
- Maintain a `tools/` or `bin/` folder with Python/bash scripts that simplify agent tasks (e.g., agent_review CLI wrapper, test runners, benchmark helpers).
- Agents should be skilled at creating and documenting new helper scripts as needed.
- Include docs on effective script creation.

### Autonomous & Night-Shift Work
- Support agent loops for autonomous work via dedicated skills or docs (e.g., night-shift orchestration: how to approach tasks, use task queue, report back).
- Task queue example: TODOS.md or integrated system (e.g., Linear with CLI access).
- Periodic sweeps: Agents can review recent commits for problems/gotchas at a higher level.

### Verification, Benchmarks & Quality Gates
- Agents must run and test their changes (build, targeted tests, end-to-end where applicable).
- Use/write tests during implementation; update test docs/lists.
- Custom linters/pre-commit with auto-fix (or LLM-assisted fix for complex cases) — focus on actually cleaning code, not just flagging.
- Periodic audits: false-confidence test reviews (tests that don't actually test what they claim), performance benchmarks/profiling.
- Visual regression (screenshots + agent review) and automatic performance degradation detection where relevant.
- End-of-shift or major milestone full validations: run tests, reviews, sweeps, benchmarks, etc.

### Feedback & Continuous Improvement
- Agents should provide automatic end-of-session feedback (what worked, issues, suggestions), committed to a reviewable doc.
- Periodically ingest this feedback in interactive sessions to refine workflows, skills, and docs.
- Combine with harness engineering principles: focus on scaffolding, context, verification, observability, and constraints around the model for reliability.

These practices draw from production agentic setups and harness engineering resources. Adapt and extend via skills in `bootstrap/grok-cli/skills/` and project templates. Prioritize composable, controllable elements over monolithic frameworks.

Reference related resources: Learn Harness Engineering site, Matt Pocock skills (planning/TDD/review via paths), gstack **role patterns** (docs only — [gstack-role-recipes.md](docs/ops/gstack-role-recipes.md)), and repo process docs for implementation.