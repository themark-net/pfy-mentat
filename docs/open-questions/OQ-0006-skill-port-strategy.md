# OQ-0006: Skill port strategy for external packs

- **Priority:** P1
- **Status:** open
- **Created:** 2026-07-12
- **Updated:** 2026-07-12
- **Blocks:** T-0011, T-0014
- **Blocked-by:** —
- **Related-ADR:** ADR-0003 (pins / no bloat)
- **Related-code:** `bootstrap/grok-cli/skills/`, `skills-external/`
- **Feature/runbook:** skill-ports
- **Related-TODO:** T-0011, T-0014

**Question:** How do we bring mattpocock/skills, marketing-council, and gstack patterns into the Grok stack?

**Context:** Large upstream skill trees (especially gstack) must not be full-embedded. ponytail already uses skills.paths snapshot model.

**Options:**

1. **Minimal first-party ports** — rewrite 1–3 skills as first-party under `bootstrap/grok-cli/skills/` (recommended default)
2. **skills.paths snapshots** — vendor selected upstream `SKILL.md` trees like ponytail
3. **Docs-only references** — TOOLS.md + AGENTS.md recipes only; no install
4. **Hybrid** — first-party for core process; paths snapshot for bulk libraries

**Recommendation:** **(4)** Hybrid: first-party for marketing-council + 1–2 plan/review skills; paths snapshot for a curated mattpocock subset; gstack as role-router docs + optional later ports.

**Resolution notes:**

- (awaiting operator choice)
