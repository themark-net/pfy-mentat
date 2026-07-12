# OQ-0009: Default WRITE_GUARD_MODE for new environments

- **Priority:** P1
- **Status:** answered
- **Created:** 2026-07-12
- **Updated:** 2026-07-12
- **Blocks:** T-0031 (write-guard MCP default behavior)
- **Related-ADR:** ADR-0007
- **Related-code:** `bootstrap/env/`, `harness/write-guard-mcp/`
- **Related-TODO:** T-0031

**Question:** For `make env-init` defaults, should write-guard start in `audit` or `enforce`?

**Context:** Cage already limits FS to `/workspace`. Write-guard adds deny-globs for secrets and audit. `enforce` is safer for unattended agents; `audit` is less surprising for interactive host ops.

**Options:**

1. **`audit` default** (recommended) — log writes; operators promote to enforce per profile (`local-only` already suggests enforce in profile file)
2. **`enforce` default** — safest; may block legitimate agent writes until policy tuned
3. **Profile-specific only** — no global default; require explicit mode

**Recommendation:** (1) global default `audit`; `local-only` profile already sets `enforce` in `config/profiles/local-only.env`.

**Resolution notes:**

- 2026-07-12: Adopted **option 1 — `audit` default** for `env.example` / REGISTRY / MCP overlay. Profile `local-only` may still set `WRITE_GUARD_MODE=enforce`. Implemented with T-0031 (`harness/write-guard-mcp/`).
