# TODO — next steps

**Purpose:** Single ordered work queue for humans and agents.  
**Design:** [DESIGN.md](DESIGN.md) · **ADRs:** [adr/](adr/README.md) · **Open questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

**Status:** `todo` | `doing` | `blocked` | `done` | `cancelled`  
**Rule:** If blocked on a decision or unknown, link an **OQ-**** ID. Do not invent architecture in a TODO row—use `/adr` when settling.

## Active

| ID | Priority | Status | Item | Open questions | Notes |
|----|----------|--------|------|----------------|-------|
| T-0001 | P0 | blocked | Complete seed X post intake (content → score → tracking method) | [OQ-0001](open-questions/OQ-0001-seed-x-post-content.md) | Placeholder still in `sources/x-posts.md` |
| T-0002 | P1 | todo | Add first real aggregate **or** high-value individual tool via SUBTREES/aggregates workflows | OQ-0001 (may inform source) | Prefer pin default (ADR-0003) |
| T-0003 | P1 | todo | Prototype evaluation harness (stack TBD) | [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | Target `examples/` or `pipelines/` |
| T-0004 | P2 | todo | Clarify ATG prototype vs catalog coupling in TOOLS/integration notes | [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | External repo exists |
| T-0005 | P2 | todo | Optionally embed first tool only if SUBTREES criteria met | [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | Do not force |
| T-0006 | P2 | todo | Module operator docs for `bootstrap/grok-cli` via `/docs` | — | install path already in README |
| T-0007 | P2 | todo | Optional: document adr-tools as companion only if a team requests CLI numbering | — | evaluation says not required |

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
