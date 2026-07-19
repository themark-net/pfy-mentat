# Evaluation Framework for Local LLM Dev Tools Catalog

**Status:** v1.2 — 2026-07-16  
**Purpose:** Consistent triage → score → optional implementation into the **Grok + agent-cage** operator stack.

**Operator defaults:** Grok Build CLI ([ADR-0002](adr/0002-grok-cli-primary-interface.md)), agent-cage lab, LiteLLM/Ollama as needed.  
**Not default:** AgenC primary runtime ([ADR-0010](adr/0010-reject-agenc-as-primary-runtime.md)).

## Full evaluation pipeline

### Phase 0: Triage & relevance gate
- Local/self-hosted value, open source/reproducible, pipeline fit.
- Accept → Phase 1, Defer, or Reject.

### Phase 1: Initial cataloging
- Add structured entry to `sources/x-posts.md` (append; never replace the whole log).
- Triple-write when scoring: `TOOLS.md` + `data/tools.json` + sources notes.
- Capture attributes (relevance, tags, github).

### Phase 2: Attribute scoring
- Apply rubric (below).
- Update cluster notes in `docs/scoring-summary.md` when useful.

### Phase 3: Integration feasibility
- Map to: Grok skill, cage smoke, eval task, LiteLLM recipe, docs-only, or OQ.
- Effort + priority (S/A/B/C).

### Phase 4: Implementation (only when justified)
Concrete change to **this** environment, e.g.:
- first-party skill under `bootstrap/grok-cli/skills/`
- in-cage `make smoke-*` or eval task
- module/ops docs
- **not** installing demoted runtimes without ADR

Guidance checker (non-authoritative): `python3 bootstrap/setup-local-agent-env.py`

## Rubric (1–5 dimensions)

| Dimension | 5 | 3 | 1–2 |
|-----------|---|---|-----|
| Relevance to local agent workflows | Core loop/memory/safety/inference | Niche | Tangential |
| Integration ease with **Grok + cage** | Make smoke / skill path clear | Moderate glue | Poor fit / heavy embed |
| Reproducibility | Docs + install + maintained | Partial docs | Closed / fragile |
| Unique value | Clear gap vs catalog | Overlaps existing | Redundant |

**Overall priority:** S (act) · A (plan) · B (reference) · C (awareness)

## Alignment notes

- Prefer pins + smokes over subtrees ([ADR-0003](adr/0003-default-pinned-commit-tracking.md)).
- Skill ports: hybrid first-party + paths ([ADR-0009](adr/0009-skill-port-hybrid-strategy.md)).
- Empirical lab receipts beat X hype: `pipelines/smoke/*`, `pipelines/eval/*`.

## Related

- [scoring-summary.md](scoring-summary.md)  
- [CATEGORIZATION.md](../CATEGORIZATION.md)  
- [TODO.md](TODO.md) · T-0042 catalog re-score  
