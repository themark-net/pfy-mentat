# OQ-0006: Skill port strategy for external packs

- **Priority:** P1
- **Status:** answered → **promoted-to-adr** (ADR-0009)
- **Created:** 2026-07-12
- **Updated:** 2026-07-12
- **Blocks:** — (was T-0011, T-0014)
- **Blocked-by:** —
- **Related-ADR:** [ADR-0009](../adr/0009-skill-port-hybrid-strategy.md), ADR-0003, ADR-0004
- **Related-code:** `bootstrap/grok-cli/skills/`, `skills-external/`
- **Feature/runbook:** skill-ports
- **Related-TODO:** T-0011, T-0014

**Question:** How do we bring mattpocock/skills, marketing-council, and gstack patterns into the Grok stack?

**Context:** Large upstream skill trees (especially gstack) must not be full-embedded. ponytail already uses skills.paths snapshot model.

**Options:**

1. **Minimal first-party ports** — rewrite 1–3 skills as first-party under `bootstrap/grok-cli/skills/`
2. **skills.paths snapshots** — vendor selected upstream `SKILL.md` trees like ponytail
3. **Docs-only references** — TOOLS.md + AGENTS.md recipes only; no install
4. **Hybrid** — first-party for core process; paths snapshot for bulk libraries

**Recommendation:** **(4)** Hybrid.

## Resolution notes

- **2026-07-12 — Operator chose option 4 (hybrid).** Formalized in **ADR-0009**.
- **Ponytail reference:** not a product dependency for “how to write code,” but the **install/layout pattern**:
  - Snapshot under `bootstrap/grok-cli/skills-external/ponytail/`
  - Registered with Grok via **`[skills].paths`** (absolute path at install time)
  - **Not** copied into `~/.grok/skills/` (unlike first-party skills)
  - Refresh via documented rsync; pin recorded in `manifest.json`
  - Opt-out: `--no-ponytail`
- **Can ponytail methods apply to the rest?** **Yes** for any bulk/curated upstream pack (mattpocock subset, future packs). First-party ports stay for **core** skills we own (criteria in ADR-0009).
- **What is “core”?** Skills that are process backbone, we will edit, small surface, default-on every install, and license-safe to embed — see ADR-0009 table. Examples already core: `adr`, `docs`, `open-questions`, `one-shot`, `catalog-docs`, `project-process`, `karpathy-guidelines`.
- **Phase 1 mapping:** marketing-council → first-party port; mattpocock subset → paths snapshot; gstack → docs/AGENTS first (T-0014), not full tree.
