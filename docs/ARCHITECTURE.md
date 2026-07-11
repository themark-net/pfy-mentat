# Architecture snapshot

**Last updated:** 2026-07-11  
**Design authority:** [DESIGN.md](DESIGN.md)  
**Decision authority:** [adr/](adr/README.md)

Keep this file short. If layering or boundaries change, accept an ADR and update both this snapshot and DESIGN §4.

## Purpose

Catalog + integration track for local-first LLM tooling, with a replayable Grok operator environment.

## Data flow (delivered)

```text
sources (X / aggregates / papers)
    → scoring (CATEGORIZATION rubric)
    → TOOLS.md + data/tools.json
    → integration packages (bootstrap/grok-cli today)
    → operator host (Grok + MCP memory + skills)
```

## Layout map

| Area | Path | Notes |
|------|------|--------|
| Process | `docs/` | Design, ADR, TODO, OQ |
| Catalog | `TOOLS.md`, `data/`, `sources/`, methodology md at root | Source of truth for scores |
| Bootstrap | `bootstrap/grok-cli/` | Installable skills + MCP + config merge |
| Future pipelines | `pipelines/`, `examples/` | Not delivered yet |

## Delivered vs not

| Delivered | Not yet |
|-----------|---------|
| Methodology + seed catalog | Continuous eval harness |
| Grok CLI bootstrap | Default LiteLLM compose stack |
| Process docs (ADR/TODO/OQ) | Automated dashboard from JSON |

## Extension points

- New tool → score → `TOOLS.md` + `data/tools.json` + source log
- New integration package → under `bootstrap/` or `pipelines/` with ADR if it changes stack defaults
- New process rule → ADR + update DESIGN/AGENTS.md

## Forbidden without ADR

- Second parallel decision log outside `docs/adr/`
- Embedding large upstream histories without meeting `SUBTREES.md`
- Putting secrets in catalog or docs
