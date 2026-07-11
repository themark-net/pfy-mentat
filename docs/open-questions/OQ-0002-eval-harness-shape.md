# OQ-0002: Evaluation harness shape (LiteLLM + DSPy + MCP)

- **Priority:** P1
- **Status:** tbd
- **Created:** 2026-07-11
- **Updated:** 2026-07-11
- **Blocks:** First pipeline prototype under `pipelines/` or `examples/`
- **Blocked-by:** OQ-0001 not strictly required but seed content may influence tasks
- **Related-ADR:** ADR-0002 (Grok primary), ADR-0003 (pins)
- **Related-code:** `pipelines/` (future), `examples/integration-patterns/` (future)
- **Feature/runbook:** eval-harness-mvp

**Question:** What is the minimal first eval harness: headless Grok-only, LiteLLM router + local Ollama, or DSPy modules with MCP memory hooks?

**Context:** DESIGN near-term lists LiteLLM + DSPy + MCP memory. Need a smallest path that proves catalog integration without building a platform.

**Options:**

1. **Grok headless script only** — fastest; weak local-stack story
2. **LiteLLM + Ollama smoke + one scored coding task** — matches hybrid goal
3. **DSPy optimizable module + MCP retrieve** — highest alignment, more glue

**Recommendation:** Option 2 as MVP; leave DSPy as P1 follow-on once smoke is green.

**Resolution notes:**

- (append dated notes; never delete)
