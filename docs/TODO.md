# TODO — next steps

**Purpose:** Single ordered work queue for humans and agents.  
**Design:** [DESIGN.md](DESIGN.md) · **ADRs:** [adr/](adr/README.md) · **Open questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

**Status:** `todo` | `doing` | `blocked` | `done` | `cancelled`  
**Rule:** If blocked on a decision or unknown, link an **OQ-**** ID. Do not invent architecture in a TODO row—use `/adr` when settling.

## Active

| ID | Priority | Status | Item | Open questions | Notes |
|----|----------|--------|------|----------------|-------|
| T-0010 | P0 | doing | **Catalog hygiene:** sync TOOLS.md + tools.json for mobile seeds 004–010; keep JSON valid; triple-write rule | — | See [plan-mobile-seed-integration.md](ops/plan-mobile-seed-integration.md). tools.json repaired 2026-07-12. |
| T-0001 | P1 | todo | Reconcile seed X placeholders vs real Entries 001/003 (ATG/colibri already processed) | [OQ-0001](open-questions/OQ-0001-seed-x-post-content.md) | Mostly superseded; close or retarget |
| T-0011 | P1 | todo | Phase 1 skill ports: mattpocock subset + marketing-council Grok skill | — | Pin/snapshot only (ADR-0003) |
| T-0012 | P1 | todo | LiteLLM + Ollama integration recipe under examples/ | — | litellm already in gom-jobbar venv |
| T-0013 | P1 | todo | repowise smoke vs codebase-memory efficiency comparison | — | Not installed yet |
| T-0003 | P1 | todo | Prototype evaluation harness | [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | Recommend LiteLLM+Ollama path |
| T-0014 | P2 | todo | gstack role-pattern skills / AGENTS router recipes (not full tree embed) | — | 121k-star; patterns only |
| T-0015 | P2 | todo | Optional Antigravity-Manager eval (multi-account relay) | — | GUI/desktop; only if needed |
| T-0016 | P2 | todo | Optional colibri build+serve experiment | — | Heavy weights; ask before download |
| T-0004 | P2 | todo | Clarify ATG prototype vs catalog coupling | [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | Sibling exists |
| T-0005 | P2 | todo | Optionally embed first tool only if SUBTREES criteria met | [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | Do not force |
| T-0006 | P2 | todo | Module operator docs for `bootstrap/grok-cli` via `/docs` | — | install path already in README |
| T-0007 | P2 | todo | Optional: document adr-tools as companion only if a team requests CLI numbering | — | evaluation says not required |
| T-0002 | P2 | todo | First real aggregate synthesis if needed beyond individual seeds | — | Seeds 003–010 already individual |

## Done

| ID | Priority | Status | Item | Notes |
|----|----------|--------|------|-------|
| T-0000 | — | done | Process docs bootstrap (DESIGN, ADR, TODO, OQ, AGENTS) | ADR-0001 |
| T-B001 | — | done | Grok CLI bootstrap package | ADR-0004; `bootstrap/grok-cli/` |
| T-B002 | — | done | project-process scaffold + skill + evaluation | `bootstrap/project-process/`; X/community research |

## How to use

1. Pick highest-priority non-blocked `todo`.
2. If work raises uncertainty → create/update OQ; set item `blocked` if P0/P1 cannot proceed.
3. If work settles architecture → `/adr`, then mark related OQ `promoted-to-adr` or `answered`.
4. Move finished rows to **Done** (do not delete history).
