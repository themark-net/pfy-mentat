# TODO — next steps ({{PROJECT_NAME}})

**Design:** [DESIGN.md](DESIGN.md) · **ADRs:** [adr/](adr/README.md) · **Open questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

**Status:** `todo` | `doing` | `blocked` | `done` | `cancelled`  
**Rule:** If blocked on a decision or unknown, link an **OQ-**** ID. Settle architecture with `/adr`, not a TODO row alone.

## Active

| ID | Priority | Status | Item | Open questions | Notes |
|----|----------|--------|------|----------------|-------|
| T-0001 | P0 | todo | Fill DESIGN goals, vision, and system shape | | Replace template placeholders |
| T-0002 | P1 | todo | Record first domain-specific ADRs as choices land | | Keep rejected alternatives |
| T-0003 | P1 | todo | Seed OPEN_QUESTIONS for known unknowns | | Use detail files when long |

## Done

| ID | Priority | Status | Item | Notes |
|----|----------|--------|------|-------|
| T-0000 | — | done | Process docs scaffolded | Via project-process bootstrap |

## How to use

1. Pick highest-priority non-blocked `todo`.
2. Uncertainty → create/update OQ; set item `blocked` if P0/P1 cannot proceed.
3. Settled architecture → `/adr`, then mark related OQ `promoted-to-adr` or `answered`.
4. Move finished rows to **Done** (do not delete history).
