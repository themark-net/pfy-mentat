# ATG coupling (Atomic Task Graph prototype)

**Status:** T-0004 / issue #22 — OQ-0004 answered 2026-07-30  
**Prototype:** https://github.com/themark-net/atg-framework  
**Paper:** https://arxiv.org/abs/2607.01942  
**Integration stage:** **I1** (staged evaluation) — intended **submodule later** when mature  
**Reviews:** 2026-08-06 → issue #30 (outcome: **stay I1**)

## Relationship to pfy-mentat

| Concern | Policy |
|---------|--------|
| Catalog | List ATG as research/prototype; link atg-framework |
| Code coupling today | **None** — no pipeline hard dependency, no Make smoke requires ATG |
| Future embed | **Submodule (I4)** only after I3 value+modularity gates ([integration-stages.md](integration-stages.md)) |
| Weights / large assets | N/A (code/method, not model weights) |

## Non-goals (now)

- Do not force symbolic submodule while prototype is still in development.  
- Do not call ATG from eval-harness or cage by default.  
- Do not treat ATG as primary orchestration (Grok + OpenCode + skills remain primary).

## Uses / features / potential (I1 card)

| Field | Content |
|-------|---------|
| **Uses** | Paper-analysis workflow; DAG task decomposition experiments |
| **Features** | Explicit DAGs vs linear agent chains; parallel planning patterns |
| **Potential** | Medium — useful if prototype stabilizes as small, customizable package |
| **Non-goals** | Primary runtime; immediate I4 |

## 2026-08-06 maturity snapshot (issue #30)

- atg-framework remains **docs-only**: ARCHITECTURE, DECISIONS 0001–0010, OPEN_QUESTIONS, TODO, attribution. No `src/atg/`, no pyproject, no tests, no examples.
- Phase 0 complete; Phase 1 skeleton (graph/types/history/validation + green pytest) **not started**.
- Working tree size trivial (≪ 50 MB). No open issues on the prototype repo.
- **Decision:** stay **I1**. I2 probe has nothing executable to probe. Value + modularity gates for I3 unmet. Do not plan I4.
- **Next trigger:** after Phase-1 runnable skeleton lands, or explicit re-request. No calendar auto-reminder required.
