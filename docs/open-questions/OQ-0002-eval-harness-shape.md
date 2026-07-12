# OQ-0002: Evaluation harness shape (LiteLLM + DSPy + MCP)

- **Priority:** P1
- **Status:** tbd
- **Created:** 2026-07-11
- **Updated:** 2026-07-12
- **Blocks:** T-0003 (eval harness prototype), informs T-0012 / T-0021
- **Blocked-by:** —
- **Related-ADR:** ADR-0002 (Grok primary)
- **Related-code:** `examples/`, `pipelines/`, `harness/agent-cage/`
- **Feature/runbook:** eval-harness-mvp
- **Related-TODO:** T-0003, T-0012, T-0021

**Question:** What is the minimal first eval harness?

**Context:** DESIGN near-term lists LiteLLM + DSPy + MCP. agent-cage is now the isolation lab. Need smallest path that proves catalog integration.

**Options:**

1. **Grok headless script only** — fastest; weak local-stack story
2. **LiteLLM + Ollama smoke + one scored coding task** (inside or outside cage) — matches hybrid goal **(recommended)**
3. **DSPy optimizable module + MCP retrieve** — highest alignment, more glue
4. **All smokes only inside agent-cage** — best isolation; depends on OQ-0005 for Grok

**Recommendation:** Option 2 as MVP; run smokes via agent-cage when T-0020 complete; leave DSPy as P1 follow-on.

**Resolution notes:**

- 2026-07-12: Operator one-shot Track A assumed **option 2** (LiteLLM + Ollama smoke, no full eval harness). In-cage smoke green via `make smoke-litellm-ollama` (host gateway :11435, policy `coding-agent-local`, model `deepseek-coder:latest`). Full DSPy/eval harness still open (T-0003).
