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

---

## Active (sorted P0 → P3, then ID)

| ID | Priority | Status | Item | Open questions | Depends | Notes |
|----|----------|--------|------|----------------|---------|-------|
| T-0020 | P0 | doing | **agent-cage harness:** complete first lab path (`up-mcp` + `test` + document) | [OQ-0005](open-questions/OQ-0005-grok-in-cage-strategy.md) | — | Scaffold + `make setup` done; full cage smoke not finished |
| T-0021 | P1 | blocked | Cage smoke-integration + first tool smokes (LiteLLM, MCP memory, repowise) | [OQ-0005](open-questions/OQ-0005-grok-in-cage-strategy.md), [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | T-0020 | Wait until cage up-mcp verified |
| T-0012 | P1 | todo | LiteLLM + Ollama integration recipe under `examples/` | [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | — | litellm already in gom-jobbar venv; prefer cage later |
| T-0011 | P1 | blocked | Phase 1 skill ports: mattpocock subset + marketing-council Grok skill | [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | — | Need port strategy choice |
| T-0013 | P1 | todo | repowise smoke vs codebase-memory efficiency comparison | — | T-0021 (preferred) | Can start host-side if cage delayed |
| T-0003 | P1 | blocked | Prototype evaluation harness | [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | T-0012 | Shape TBD; recommend LiteLLM+Ollama smoke |
| T-0022 | P2 | blocked | Grok-in-cage or host-Grok+workspace overlay | [OQ-0005](open-questions/OQ-0005-grok-in-cage-strategy.md) | T-0020 | overlays/ planned |
| T-0014 | P2 | blocked | gstack role-pattern skills / AGENTS router recipes | [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | T-0011 | Patterns only; no full tree embed |
| T-0015 | P2 | blocked | Optional Antigravity-Manager eval | [OQ-0007](open-questions/OQ-0007-antigravity-need.md) | — | Only if multi-account pain |
| T-0016 | P2 | blocked | Optional colibri build+serve experiment | [OQ-0008](open-questions/OQ-0008-colibri-weights-ok.md) | — | Heavy weights; explicit OK required |
| T-0004 | P2 | blocked | Clarify ATG prototype vs catalog coupling | [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | — | Sibling `atg-framework` exists |
| T-0005 | P2 | blocked | Optionally embed first tool (subtree/submodule) | [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | — | Default remains pin (ADR-0003) |
| T-0006 | P2 | todo | Module operator docs for `bootstrap/grok-cli` (+ harness) via `/docs` or `/catalog-docs module` | — | README covers install; module docs still thin |
| T-0007 | P3 | todo | Document adr-tools as companion only if a team requests CLI numbering | — | Evaluation: not required by default |
| T-0002 | P3 | todo | First real aggregate synthesis if needed beyond individual seeds | — | Seeds 003–010 already individual |

---

## Done

| ID | Priority | Status | Item | Notes |
|----|----------|--------|------|-------|
| T-0000 | — | done | Process docs bootstrap (DESIGN, ADR, TODO, OQ, AGENTS) | ADR-0001 |
| T-B001 | — | done | Grok CLI bootstrap package | ADR-0004 |
| T-B002 | — | done | project-process scaffold + skill + evaluation | bootstrap/project-process |
| T-B003 | — | done | `/catalog-docs` skill + README v0.4 | 2026-07-12 |
| T-0010 | P0 | done | Catalog hygiene: triple-write seeds 004–010 + agent-cage row | Phase 0; tools.json repaired |
| T-0001 | P1 | done | Reconcile seed X placeholders vs Entries 001/003 | Superseded by processed seeds; OQ-0001 closed |

## How to use

1. Scan **Open questions** index; do not silently answer P0/P1.
2. Pick highest-priority non-blocked Active row.
3. Uncertainty → create/update OQ; set TODO `blocked` if P0/P1 cannot proceed.
4. Settled architecture → `/adr`, then OQ `promoted-to-adr` or `answered`.
5. Finish → Status `done`, move row to **Done**.
