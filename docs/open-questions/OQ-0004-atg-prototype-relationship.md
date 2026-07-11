# OQ-0004: How ATG prototype relates to this catalog

- **Priority:** P2
- **Status:** open
- **Created:** 2026-07-11
- **Updated:** 2026-07-11
- **Blocks:** Clear integration notes / optional pipeline experiment
- **Blocked-by:** —
- **Related-ADR:** —
- **Related-code:** TOOLS.md ATG row; external https://github.com/themark-net/atg-framework
- **Feature/runbook:** paper-analysis-workflow

**Question:** Is `atg-framework` a sibling experiment only, a future submodule, or the reference implementation that pipelines here should call?

**Context:** Paper analysis workflow created a dedicated prototype repo. Catalog still lists ATG as paper-based with prototype link. Ownership and coupling are unclear for agents.

**Options:**

1. **Sibling only** — catalog links; no code coupling
2. **Submodule later** if small and customized here
3. **Pinned dependency** from a future harness package

**Recommendation:** Sibling only until harness design (OQ-0002) needs it; document in TOOLS notes when chosen.

**Resolution notes:**

- (append dated notes; never delete)
