# Design: pfy-mentat

**Status:** Active  
**Last updated:** 2026-07-11  
**Authority for *why*:** [docs/adr/](adr/README.md)  
**Next work:** [docs/TODO.md](TODO.md) · open items [docs/OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

This is the **master design document**: primary goals, intended shape of the system, and how pieces fit. It describes intent and boundaries. Settled architecture choices live in ADRs; day-to-day work lives in TODO + open questions.

---

## 1. Vision

Build a **living, scored catalog** of local-first LLM development tools and a **reproducible operator stack** so humans and agents can evaluate, integrate, and run continuous local pipelines—with **Grok CLI** as the primary interface and MCP-style code memory in the loop.

One-line purpose: **Track · Categorize · Rank · Integrate** tools for robust self-hosted agentic development.

---

## 2. Primary goals

| # | Goal | Success looks like |
|---|------|--------------------|
| G1 | Living catalog | Scored tools in `TOOLS.md` + `data/tools.json`, sourced from X/community with rubric integrity |
| G2 | Consistent evaluation | Stage 0 gate + weighted Stages 1–4 (see `CATEGORIZATION.md`); tiers S/A/B/C stay comparable over time |
| G3 | Stack synergies | Clear recommended combos (e.g. Grok + LiteLLM + Ollama + MCP memory + DSPy) documented with integration notes |
| G4 | Rapid integration | Highest-value components installable/replayable without repo bloat (pins, rare subtree, bootstrap) |
| G5 | Grok-first interface | Operator env and agent skills bootstrapped from this repo; hybrid/fallback to other harnesses when scored higher for a task |
| G6 | Lean tracking | Prefer pinned SHA + shallow clone; embed only when criteria in `SUBTREES.md` are met |
| G7 | Durable process | Design + ADR + TODO + open questions keep multithreaded agents from re-litigating or losing TBDs |

---

## 3. Non-goals (current horizon)

- Becoming a monorepo of large inference engines or full IDE products
- Auto-submitting external systems or holding user secrets in-repo
- Replacing Grok’s own binary, auth, or marketplace plugins
- Exhaustive “awesome list” coverage without scoring or pipeline value

---

## 4. System shape

```text
                    ┌─────────────────────────────────────┐
  X posts / papers  │  Intake                             │
  aggregates        │  sources/x-posts.md                 │
                    │  sources/aggregates.md              │
                    └──────────────┬──────────────────────┘
                                   │ score + synthesize
                    ┌──────────────▼──────────────────────┐
                    │  Catalog                            │
                    │  TOOLS.md  ·  data/tools.json       │
                    │  CATEGORIZATION.md rubric           │
                    └──────────────┬──────────────────────┘
                                   │ integrate
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
   bootstrap/grok-cli/      pipelines/ (future)      examples/ (future)
   skills · MCP · config    eval harnesses           compose / patterns
          │
          ▼
   Operator machine: Grok CLI + codebase-memory + agent skills
          │
          ▼
   Downstream projects (e.g. gom-jobbar, ATG prototype) consume stack
```

### Layers

| Layer | Location | Role |
|-------|----------|------|
| Process | `docs/` | Design, ADR, TODO, open questions |
| Catalog methodology | `CATEGORIZATION.md`, `SUBTREES.md` | How to score and track tools |
| Catalog content | `TOOLS.md`, `data/tools.json`, `sources/` | What is scored and where it came from |
| Integration packages | `bootstrap/`, later `pipelines/`, `examples/` | How to run / replay stack pieces |
| External tools | pins / rare `tools/` embeds | Upstream code not owned here |

---

## 5. Delivered vs future

### Delivered

- Catalog methodology (taxonomy, rubric, subtree policy, aggregates intake)
- Seeded scored tools + paper analysis workflow (ATG)
- First-party **Grok CLI bootstrap** (`bootstrap/grok-cli/`)
- Process docs layout (this file + ADR + TODO + OQ)
- **project-process bootstrap** (`bootstrap/project-process/`) — replayable scaffold + `/project-process` skill for new repos
- Phase 0 catalog sync for mobile seeds 003–010 + **agent-cage** as primary container harness (`harness/agent-cage/`)
- agent-cage baseline smoke green (policy tests); root `make cage-*` UX
- **Deployment profiles** + env registry (`local-only` / `balanced` / `max-performance`) — ADR-0006
- **Write-guard MCP design** (filesystem write mediation) — ADR-0007; implement next
- **One-shot workflow** — minimize questions; cheap iteration; lab prerequisites — ADR-0008 · `/one-shot`

### Near-term (see TODO)

Active queue is mostly **blocked P2** decisions + **T-0040** (other harness validation). Natural follow-ons after MVP lab:

- Catalog re-score pass using smokes + `make eval-v02` / matrix
- Write-guard → mcp-host default wiring (server already green)
- Unlock one blocked P2 (OQ-0003 / 0004 / 0007 / 0008)

### Delivered recently (was near-term)

- Write-guard MCP v0.1 + cage smoke · in-cage tool smokes · LiteLLM profile recipes · skill ports (ADR-0009) · eval harness MVP + v0.2 suite/matrix (OQ-0002 / T-0041) · grok-in-image overlay (**OQ-0005 answered**)

### Later / research

- Automated scoring dashboard from `data/tools.json`
- Continuous pipeline CI for agent evals
- Hybrid local model routing defaults as scored recipes
- DSPy + MCP scored tier (post eval MVP)

---

## 6. Process model (mandatory for agents)

| Artifact | Path | Holds |
|----------|------|--------|
| **Design** (this doc) | `docs/DESIGN.md` | Goals, shape, boundaries |
| **Architecture map** | `docs/ARCHITECTURE.md` | Current structural snapshot (keep short; link here) |
| **ADR** | `docs/adr/` | Settled *why*, including **rejected** alternatives |
| **TODO** | `docs/TODO.md` | Ordered next steps; links to OQs |
| **Open questions** | `docs/OPEN_QUESTIONS.md` + optional `docs/open-questions/` | Unsettled TBDs; context may also live next to the code/doc that raised them |
| **Operator/agent module docs** | `docs/modules/`, `docs/ops/` | How to run / navigate non-trivial modules (via `/docs` skill) |

### Rules

1. **Read before design changes:** `docs/DESIGN.md` + open ADRs + relevant OQs.
2. **Architecture pivots → ADR:** record decision, rationale, and **paths decided against** so they are not re-followed without re-examining context.
3. **Work items → TODO:** central next steps; each item may reference OQ IDs.
4. **Uncertainty → Open Question:** when work raises a TBD, add/update an OQ (central index required). Prefer a **detail file** or a short note **in the module/doc context** that links back to the OQ ID—do not leave questions only in chat.
5. **Answered architectural OQs → promote to ADR** (`promoted-to-adr`).

Skills (installed via bootstrap): `/adr`, `/open-questions` (`/oq`), `/docs`.

---

## 7. External ownership boundaries

| System | This repo may | This repo must not |
|--------|---------------|--------------------|
| Grok CLI | Ship skills, config fragments, install scripts | Store `auth.json`, API keys, session DBs |
| Upstream tools | Pin, score, rarely embed | Fork large runtimes into default path |
| Sibling projects | Reference, bootstrap against | Silently mutate sacred user data |
| X / papers | Log sources, synthesize catalog rows | Claim ownership of third-party IP |

---

## 8. Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — structural snapshot
- [adr/README.md](adr/README.md) — decision index
- [TODO.md](TODO.md) — next steps
- [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) — parking lot
- Root: `README.md`, `CATEGORIZATION.md`, `SUBTREES.md`, `TOOLS.md`
- Bootstrap: `bootstrap/grok-cli/README.md`
