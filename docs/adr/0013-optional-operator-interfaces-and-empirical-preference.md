# ADR-0013: Treat operator interfaces (including AgenC TUI) as optional scored components; introduce empirical preference dimension

- **Date:** 2026-07-27
- **Status:** Accepted
- **Supersedes:** the absolute “not primary / catalog-only” posture of [ADR-0010](0010-reject-agenc-as-primary-runtime.md) regarding the full AgenC surface
- **Related:** [ADR-0002](0002-grok-cli-primary-interface.md) (Grok CLI primary — **affirmed as default**), [ADR-0011](0011-hybrid-operator-surfaces-grok-opencode-ollama.md), OQ on preference measurement

## Context

ADR-0010 recorded a valid early operator trial (2026-07-12) in which the AgenC TUI exhibited high friction: obscure approval prompts, repeated prompts for ordinary reads and tooling, and an auth surface that did not align cleanly with an existing Grok Build subscription. Those observations remain useful data.

However, treating any single interface surface as a permanent binary disqualifier for an entire system under-weights modularity. The same rails (protocol, marketplace, MCP, worker) can be used with the TUI completely bypassed. The project goal of standardized measurement of fit for *any* tool — harness, MCP, agent, loop, graph, **or interface** — requires that TUIs and operator surfaces themselves be treated as optional, independently scoreable parts.

Developer preference is real. It is also empirical. It cannot be known a priori from a short trial or from documentation alone. It only becomes measurable after actual deployment and repeated use. Leaving preference unmeasured leaves an important fit signal outside the rubric.

## Decision

1. **Grok CLI + agent-cage remain the default primary** operator path for this repository (ADR-0002 and related decisions affirmed).
2. The full AgenC surface (protocol + marketplace + MCP + worker + **optional** TUI) is a **first-class scored alternative**. The TUI itself is optional and can be ignored completely in favor of CLI / MCP / worker paths.
3. **Operator Interface Fit / Preference** is introduced as a post-deployment empirical dimension in the rubric. Initial values are blank or “pending real use”; scores are filled only from actual operator hours, task receipts, or explicit preference logs.
4. Catalog entries for interface-heavy tools (including AgenC) must note optionality of the TUI explicitly and leave preference scores to be populated from deployment data.
5. **Isolation / sandbox patterns remain a distinct concern.** agent-cage continues as the primary general-purpose local isolation and reproducibility lab. AgenC’s sandboxing and security mechanisms are marketplace-oriented (tied to identity, escrow, and on-chain participation) and **do not supersede or fully duplicate** agent-cage. Strengthen “local agent isolation / harness security” as its own subcategory or weighted factor under Stage 3 (or a dedicated Security/Harness dimension).

## Consequences

- This ADR supersedes the hard “catalog only / not primary” language of ADR-0010 for the full surface while preserving the original trial data as historical preference input.
- Update `CATEGORIZATION.md` with the new empirical preference dimension and a note on isolation as a distinct category.
- Update the AgenC row in `TOOLS.md` and `data/tools.json` to first-class optional status (TUI optional, preference pending empirical data).
- Bootstrap, skills, and hybrid profiles may surface AgenC as a selectable operator surface without making it the default.
- Evaluation lanes, one-shot, and agent-loops workflows should be extended to capture preference receipts after real runs.
- agent-cage isolation remains the primary scored example for general local harness security; AgenC isolation is noted as marketplace-specific.

## Rejected alternatives

1. **Silent amendment of ADR-0010** — loses clear decision history; violates the “never silent overwrite” rule.
2. **Making AgenC co-primary or the new default** — contradicts current operator preference data and ADR-0002.
3. **Ignoring preference as a signal** — leaves an important, real-world fit dimension unmeasured.
4. **Treating all TUIs as non-scoreable** — breaks the standardization goal of measuring every component for fit.
5. **Claiming AgenC supersedes agent-cage** — incorrect scope; the two address overlapping but non-identical isolation needs.

## References

- ADR-0010 (historical trial and original decision)
- ADR-0002, ADR-0011
- `harness/agent-cage/`, `bootstrap/agenc/`, `integration/agenc/`
- Upstream: https://github.com/tetsuo-ai/AgenC, https://agenc.tech/
