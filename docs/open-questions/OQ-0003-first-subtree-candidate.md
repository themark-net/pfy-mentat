# OQ-0003: First subtree/submodule candidate

- **Priority:** P2
- **Status:** answered
- **Created:** 2026-07-11
- **Updated:** 2026-07-30
- **Blocks:** — (was T-0005)
- **Blocked-by:** —
- **Related-ADR:** ADR-0003
- **Related-code:** `SUBTREES.md`, `docs/ops/integration-stages.md`
- **Feature/runbook:** selective-embed
- **Related-TODO:** T-0005 (retarget: apply integration stages; no symbolic first embed)
- **GitHub issue:** [#17](https://github.com/themark-net/pfy-mentat/issues/17)

**Question:** Which tool, if any, should be the first subtree or submodule?

**Context:** Default remains pin + shallow clone. Bootstrap already vendors small skill snapshots without full upstream history.

**Options:**

1. Wait until a small, customized MCP or harness needs in-tree edits
2. Submodule a thin eval suite once harness lands
3. Never embed; pins only (revisit if offline CI needs trees)

**Recommendation:** Wait (1); do not force a symbolic first embed.

**Resolution notes:**

- **2026-07-30 — Wait.** No first subtree/submodule candidate. Define thresholds and a separate **integration-stage** rubric rather than jumping to embed:
  - **Value gate** and **modularity gate** for promotion toward onboard.
  - Until full onboard, tools stay in **staged evaluation (I1)**: catalog uses, features, potential, non-goals.
  - If potential is **ambiguous** and the tree is **lightweight (< ~50 MB, no weights)**, may use **I2 ad-hoc probe** copy for further eval — **not** “integration.”
  - **I3 onboard / integrated** only after gates; **I4 embed** still rare per SUBTREES.md + ADR-0003.
  - Canonical doc: [docs/ops/integration-stages.md](../ops/integration-stages.md).
