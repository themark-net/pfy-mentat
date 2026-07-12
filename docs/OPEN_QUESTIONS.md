# Open Questions

**Purpose:** Central index of open questions, TBDs, and parked decisions for multithreaded work.  
Agents: scan this file at the start of multi-step work. Promote architectural answers via `/adr`.

## Qualification model

| Field | Values | Meaning |
|-------|--------|---------|
| **Priority** | `P0` / `P1` / `P2` / `P3` | Same scale as TODO: P0 blocks critical path |
| **Status** | `open` \| `blocked` \| `tbd` \| `answered` \| `promoted-to-adr` \| `wont-do` | `tbd` = parked with enough context for another agent; `open` = needs attention |
| **Blocks** | workstream or T-IDs | What cannot finish until this is resolved |
| **Related** | ADR, code paths, T-IDs | Graph edges |

**In-context rule:** When a question arises in code or docs, add a central row (and optional `docs/open-questions/OQ-NNNN-slug.md`) **or** a local note citing **`OQ-NNNN`**. Never leave P0–P2 only in chat.

Related work queue: [TODO.md](TODO.md)

---

## Index (active + recent)

| ID | Priority | Status | Title | Blocks | Related |
|----|----------|--------|-------|--------|---------|
| [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | **P1** | tbd | Evaluation harness shape (LiteLLM + DSPy + MCP?) | T-0003, T-0012, T-0021 | ADR-0002 |
| [OQ-0005](open-questions/OQ-0005-grok-in-cage-strategy.md) | **P1** | open | Grok vs Claude-in-cage vs host-Grok + cage workspace | T-0020, T-0021, T-0022 | harness/agent-cage |
| [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | **P1** | open | Skill port strategy: first-party ports vs skills.paths snapshots vs docs-only | T-0011, T-0014 | ADR-0003, bootstrap skills |
| [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | P2 | tbd | First subtree/submodule candidate (if any) | T-0005 | SUBTREES.md, ADR-0003 |
| [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | P2 | open | How ATG prototype relates to this catalog | T-0004 | atg-framework, TOOLS.md |
| [OQ-0007](open-questions/OQ-0007-antigravity-need.md) | P2 | tbd | Do we need Antigravity-Manager multi-account relay? | T-0015 | LiteLLM, hybrid accounts |
| [OQ-0008](open-questions/OQ-0008-colibri-weights-ok.md) | P2 | tbd | OK to download colibri model weights on this machine? | T-0016 | disk/RAM, colibri pin |
| [OQ-0009](open-questions/OQ-0009-write-guard-default-mode.md) | P1 | answered | Default WRITE_GUARD_MODE for new envs (audit vs enforce) | T-0031 | ADR-0007; default **audit** |
| [OQ-0001](open-questions/OQ-0001-seed-x-post-content.md) | P3 | answered | Seed X post content extraction | — | Superseded by Entries 001–010 processed |

---

## Needs operator input soon (P1)

1. **OQ-0005** — Grok in-image vs host-Grok + cage (default: host-Grok until overlay built).  
2. **OQ-0006** — Skill port strategy (default: hybrid).  
3. **OQ-0002** — Eval harness MVP = LiteLLM + Ollama smoke (recommended).  
4. ~~**OQ-0009** — Write-guard default~~ → **answered: audit**.

## Hygiene

- Re-scan this table when starting a milestone; close or re-prioritize stale P0/P1s.
- When answering: append dated **Resolution notes** in the detail file; set Status; promote architecture to `/adr`.
