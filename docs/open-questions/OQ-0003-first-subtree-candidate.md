# OQ-0003: First subtree/submodule candidate

- **Priority:** P2
- **Status:** tbd
- **Created:** 2026-07-11
- **Updated:** 2026-07-11
- **Blocks:** First use of embed path under `tools/`
- **Blocked-by:** No candidate yet meeting SUBTREES.md all-criteria gate
- **Related-ADR:** ADR-0003
- **Related-code:** `SUBTREES.md`, future `tools/`
- **Feature/runbook:** selective-embed

**Question:** Which tool, if any, should be the first subtree or submodule?

**Context:** Default remains pin + shallow clone. Bootstrap already vendors small skill snapshots without full upstream history.

**Options:**

1. Wait until a small, customized MCP or harness needs in-tree edits
2. Submodule a thin eval suite once harness lands
3. Never embed; pins only (revisit if offline CI needs trees)

**Recommendation:** Wait (1); do not force a symbolic first embed.

**Resolution notes:**

- (append dated notes; never delete)
