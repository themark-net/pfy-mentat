# OQ-0007: Do we need Antigravity-Manager?

- **Priority:** P2
- **Status:** answered
- **Created:** 2026-07-12
- **Updated:** 2026-07-30
- **Blocks:** — (was T-0015)
- **Blocked-by:** —
- **Related-ADR:** —
- **Related-code:** TOOLS.md Antigravity-Manager row
- **Feature/runbook:** hybrid-accounts
- **Related-TODO:** T-0015 (low-priority catalog eval only)
- **GitHub issue:** [#19](https://github.com/themark-net/pfy-mentat/issues/19)

**Question:** Is multi-account web-session → local API relay a real pain for this stack, or is LiteLLM + API keys enough?

**Context:** Antigravity-Manager is a large desktop app. Value is high only if juggling browser-login AI tools / quotas.

**Options:**

1. **Skip for now** — LiteLLM + keys (recommended until pain is felt)
2. **Eval Tauri binary** on a GUI machine
3. **Pin and document only** — no install

**Recommendation:** (1) or (3) until multi-account pain is explicit.

**Resolution notes:**

- **2026-07-30 — Skip for now (option 1).** Keep in evaluation / catalog pipeline at **lower priority** than higher-opportunity work. LiteLLM + API keys remain default. No install; no blocked track.
- **Process note:** This should not have been a **blocking OQ**. It is an optional tool-adopt case with a safe reversible default (skip runtime). See [human-decision-inventory.md](../ops/human-decision-inventory.md) § “When to open an OQ” and [integration-stages.md](../ops/integration-stages.md) I1 defaults. Future similar items: catalog **I1** + default **skip install** + priority P3; escalate to OQ only if operator reports multi-account pain or wants install/weights/embed.
