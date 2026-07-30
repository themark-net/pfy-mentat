# ATG coupling (Atomic Task Graph prototype)

**Status:** T-0004 / issue #22 — OQ-0004 answered 2026-07-30  
**Prototype:** https://github.com/themark-net/atg-framework  
**Paper:** https://arxiv.org/abs/2607.01942  
**Integration stage:** **I1** (staged evaluation) — intended **submodule later** when mature  
**Review:** 2026-08-06 → issue #30

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

## Follow-up checklist (issue #30)

1. Maturity / size / API of atg-framework  
2. Stay I1 / I2 probe (<50 MB) / plan I3→I4 submodule  
3. Update TOOLS.md + tools.json notes
