# OQ-0004: How ATG prototype relates to this catalog

- **Priority:** P2
- **Status:** answered
- **Created:** 2026-07-11
- **Updated:** 2026-07-30
- **Blocks:** — (was T-0004)
- **Blocked-by:** —
- **Related-ADR:** ADR-0003 · integration-stages.md
- **Related-code:** TOOLS.md ATG row; external https://github.com/themark-net/atg-framework
- **Feature/runbook:** paper-analysis-workflow
- **Related-TODO:** T-0004 (document coupling; plan submodule when ATG matures)
- **GitHub issue:** [#18](https://github.com/themark-net/pfy-mentat/issues/18)
- **Follow-up:** ~2026-08-06 review (issue + scheduled reminder)

**Question:** Is `atg-framework` a sibling experiment only, a future submodule, or the reference implementation that pipelines here should call?

**Context:** Paper analysis workflow created a dedicated prototype repo. Catalog still lists ATG as paper-based with prototype link. Ownership and coupling are unclear for agents.

**Options:**

1. **Sibling only** — catalog links; no code coupling
2. **Submodule later** if small and customized here
3. **Pinned dependency** from a future harness package

**Recommendation:** Sibling only until harness design (OQ-0002) needs it; document in TOOLS notes when chosen.

**Resolution notes:**

- **2026-07-30 — Option 2: Submodule later.** ATG is **still in development**. Intent is a future **submodule** (I4 path) once the prototype is mature enough — not “sibling forever,” not immediate embed.
  - **Now:** treat as **I1 staged evaluation** in the catalog (link + pin when available; uses/features/potential notes). No code coupling until review.
  - **Gate for submodule:** clear I3 value+modularity (or justified I2 probe if <50 MB and potential still ambiguous), then SUBTREES.md embed checklist.
  - **Reminder:** revisit ~**2026-08-06** (one week) to assess readiness for probe/submodule work.
