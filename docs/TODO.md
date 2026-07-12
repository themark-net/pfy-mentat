# TODO — next steps

**Purpose:** Single ordered work queue for humans and agents.  
**Design:** [DESIGN.md](DESIGN.md) · **ADRs:** [adr/](adr/README.md) · **Open questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

## Qualification model

| Field | Values | Meaning |
|-------|--------|---------|
| **Priority** | `P0` / `P1` / `P2` / `P3` | P0 = blocks current critical path · P1 = next milestone · P2 = important not blocking · P3 = someday |
| **Status** | `todo` \| `doing` \| `blocked` \| `done` \| `cancelled` | Active work only in **Active** table; finished rows move to **Done** |
| **Open questions** | `OQ-NNNN` or `—` | **Required** if Status is `blocked` or if work needs a human decision before P0/P1 can finish |
| **Depends** | T-IDs | Optional ordering edges |

**Rules**

1. Every `blocked` row **must** cite an OQ (or external blocker named in Notes).
2. Every OQ that blocks work should appear in at least one Active TODO’s **Open questions** column.
3. Do not invent architecture in a TODO — settle with `/adr`.
4. Never delete history; move finished rows to **Done**.
5. New tool integrations: register env vars in `bootstrap/env/REGISTRY.md`; prefer smokes **inside agent-cage**.

---

## Active (sorted P0 → P3)

| ID | Priority | Status | Item | Open questions | Depends | Notes |
|----|----------|--------|------|----------------|---------|-------|
| T-0012 | P1 | doing | LiteLLM + Ollama recipe under `examples/` keyed by DEPLOY_PROFILE | [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | T-0030 | **local-only MVP shipped** (`examples/litellm-ollama/`, `make smoke-litellm-ollama`); balanced/max recipes still open |
| T-0011 | P1 | blocked | Phase 1 skill ports: mattpocock subset + marketing-council | [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | — | Need port strategy |
| T-0003 | P1 | blocked | Prototype evaluation harness | [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | T-0012 | |
| T-0040 | P3 | todo | **Nice-to-have:** validate integrated setup with OpenCode and Claude Code (same cage/profiles/env) | — | — | Universal harness goal; Grok-first for now |
| T-0014 | P2 | blocked | gstack role-pattern skills / AGENTS recipes | [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | T-0011 | |
| T-0015 | P2 | blocked | Optional Antigravity-Manager eval | [OQ-0007](open-questions/OQ-0007-antigravity-need.md) | — | |
| T-0016 | P2 | blocked | Optional colibri build+serve | [OQ-0008](open-questions/OQ-0008-colibri-weights-ok.md) | — | |
| T-0004 | P2 | blocked | ATG prototype coupling | [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | — | |
| T-0005 | P2 | blocked | Optional first subtree | [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | — | |

| T-0007 | P3 | todo | adr-tools companion docs if requested | — | — | |
| T-0002 | P3 | todo | Aggregate synthesis if needed | — | — | |

---

## Done

| ID | Priority | Status | Item | Notes |
|----|----------|--------|------|-------|
| T-0030 | P0 | done | Env registry + profiles | merged main |
| T-0022 | P1 | done | Grok-in-image overlay | feature/agent-cage-grok-image merged; OIDC auth import |
| T-0000 | — | done | Process docs bootstrap | ADR-0001 |
| T-B001 | — | done | Grok CLI bootstrap | ADR-0004 |
| T-B002 | — | done | project-process scaffold | |
| T-B003 | — | done | `/catalog-docs` skill + README v0.4 | |
| T-0010 | P0 | done | Catalog hygiene Phase 0 | |
| T-0001 | P1 | done | Seed placeholder reconcile | OQ-0001 answered |
| T-0020 | P0 | done | agent-cage lab baseline (up-mcp + policy tests pass) | Operator smoke 2026-07-12; UX on main |
| T-0021 | P1 | done | Cage tool smokes **inside cage** (LiteLLM, MCP memory, repowise) | LiteLLM + codebase-memory + repowise; `make smoke-context-tools` |
| T-0013 | P1 | done | repowise smoke vs codebase-memory (prefer in-cage) | pipelines/smoke/context-tools-compare.md; both smokes green 2026-07-12 |
| T-0031 | P1 | done | **Write-guard MCP implement** (stdio server + cage overlay) | harness/write-guard-mcp v0.1; make smoke-write-guard; OQ-0009 audit default |
| T-0032 | P1 | done | **One-shot skill polish + example DoDs** for cage/tool smokes | docs/ops/one-shot-example-dods.md; skill points at make smoke-* |
| T-0006 | P2 | done | Module docs bootstrap + harness via `/catalog-docs` | docs/modules/* for grok-cli, project-process, agent-cage, write-guard, smokes |

## How to use

1. Scan **Open questions**; do not silently answer P0/P1.
2. Pick highest-priority non-blocked Active row.
3. Uncertainty → OQ; set TODO `blocked` if needed.
4. Architecture → `/adr`.
5. Finish → **Done** table.
