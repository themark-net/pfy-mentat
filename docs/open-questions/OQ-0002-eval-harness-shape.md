# OQ-0002: Evaluation harness shape (LiteLLM + DSPy + MCP)

- **Priority:** P1
- **Status:** answered → implemented as option **5** (T-0003 MVP)
- **Created:** 2026-07-11
- **Updated:** 2026-07-12
- **Blocks:** — (was T-0003)
- **Blocked-by:** —
- **Related-ADR:** ADR-0002 (Grok primary)
- **Related-code:** `examples/eval-harness/`, `examples/litellm-ollama/`, `pipelines/smoke/`, `harness/agent-cage/`
- **Feature/runbook:** eval-harness-mvp
- **Related-TODO:** T-0003, T-0012, T-0021

**Question:** What is the minimal first eval harness?

**Context:** DESIGN near-term lists LiteLLM + DSPy + MCP. agent-cage is the isolation lab. Connectivity smokes already exist.

**Options:**

1. **Grok headless script only** — fastest; weak local-stack story
2. **LiteLLM + Ollama smoke + one scored coding task** — matches hybrid goal
3. **DSPy optimizable module + MCP retrieve** — highest alignment, more glue
4. **All smokes only inside agent-cage** — connectivity only; weak for TOOLS re-scoring
5. **Hybrid tiers** — smokes = tier 0; one scored in-cage task = tier 1; DSPy deferred

**Recommendation (historical):** Option 2; refined to **5** after smokes shipped.

## Resolution notes

- **2026-07-12 (early):** Track A assumed option 2 for connectivity; `make smoke-litellm-ollama` green.
- **2026-07-12 (operator):** Chose **option 5**.
  - **Tier 0:** existing `make smoke-*` ladder (connectivity / install).
  - **Tier 1:** one fixed scored coding task in cage via LiteLLM→Ollama; pass/fail + `results.latest.md`.
  - **Later:** DSPy + MCP (option 3) as follow-on, not MVP.
- **Implementation:** `examples/eval-harness/` + `make eval-tier0` / `make eval-tier1` / `make eval-mvp` (T-0003).
- **Models:** tier0 keeps `LITELLM_SMOKE_MODEL` (tiny OK). Tier1 defaults to `EVAL_MODEL=qwen2.5:14b` — `deepseek-coder:latest` (~1B) is unreliable for scoring (prose/syntax).
- **Verified:** `make eval-mvp` green (2026-07-12) with SCORE: PASS on `001-is-palindrome`.
- **v0.2 (T-0041):** second task `002-fix-sum-evens`; `make eval-suite` / `eval-matrix` / `eval-v02`; gate model must pass all tasks; extra models are observational (SKIP if absent).
