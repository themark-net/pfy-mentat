# OQ-0007: Do we need Antigravity-Manager?

- **Priority:** P2
- **Status:** tbd
- **Created:** 2026-07-12
- **Updated:** 2026-07-12
- **Blocks:** T-0015
- **Blocked-by:** —
- **Related-ADR:** —
- **Related-code:** TOOLS.md Antigravity-Manager row
- **Feature/runbook:** hybrid-accounts
- **Related-TODO:** T-0015

**Question:** Is multi-account web-session → local API relay a real pain for this stack, or is LiteLLM + API keys enough?

**Context:** Antigravity-Manager is a large desktop app. Value is high only if juggling browser-login AI tools / quotas.

**Options:**

1. **Skip for now** — LiteLLM + keys (recommended until pain is felt)
2. **Eval Tauri binary** on a GUI machine
3. **Pin and document only** — no install

**Recommendation:** (1) or (3) until multi-account pain is explicit.

**Resolution notes:**

- (parked; operator can mark wont-do)
