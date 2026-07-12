# OQ-0008: OK to download colibri model weights?

- **Priority:** P2
- **Status:** tbd
- **Created:** 2026-07-12
- **Updated:** 2026-07-12
- **Blocks:** T-0016
- **Blocked-by:** —
- **Related-ADR:** ADR-0003 (no weights in catalog repo)
- **Related-code:** TOOLS.md colibri; HF weights refs in x-posts Entry 003
- **Feature/runbook:** colibri-eval
- **Related-TODO:** T-0016

**Question:** May we download large colibri/GLM int4 weights onto this machine (disk + RAM ~25GB class) for serve benchmarks?

**Context:** Engine is pinned in catalog; weights are large and tok/s is expected low. Ollama already covers day-to-day local models.

**Options:**

1. **No / park** — keep catalog pin only (recommended default)
2. **Yes, under explicit path** — e.g. external disk; document location; never commit weights
3. **Yes, later in agent-cage only** — isolate experiment

**Recommendation:** (1) until operator confirms disk budget and interest in flagship-MoE-on-laptop path.

**Resolution notes:**

- (awaiting explicit OK before any download)
