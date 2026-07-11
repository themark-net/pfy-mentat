# Open Questions

**Purpose:** Central index of open questions, TBDs, and parked decisions for multithreaded work.  
Agents: scan this file at the start of multi-step work. Promote architectural answers via `/adr`.

**Status values:** `open` | `blocked` | `tbd` | `answered` | `promoted-to-adr` | `wont-do`  
**Priority:** P0 (blocks MVP) | P1 (next milestone) | P2 | P3 (someday)

**In-context rule:** When an open question arises while writing code or docs, either:

1. Add detail under `docs/open-questions/OQ-NNNN-slug.md` and a row here, **or**
2. Add a short note in the local file (comment or doc section) that cites **`OQ-NNNN`** and ensure the central index row exists.

Never leave P0–P2 questions only in chat.

Related work queue: [TODO.md](TODO.md)

## Index

| ID | Priority | Status | Title | Blocks | Related |
|----|----------|--------|-------|--------|---------|
| [OQ-0001](open-questions/OQ-0001-seed-x-post-content.md) | P0 | open | Seed X post content extraction | Catalog seed completion | sources/x-posts.md, TODO T-0001 |
| [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | P1 | tbd | Evaluation harness shape (LiteLLM + DSPy + MCP) | Pipeline prototype | TODO T-0003, ADR-0002 |
| [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | P2 | tbd | First subtree/submodule candidate | Optional embed path | SUBTREES.md, ADR-0003 |
| [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | P2 | open | How ATG prototype relates to this catalog | Integration notes clarity | atg-framework, TOOLS.md |

## Detail

Short items may live only in detail files linked above. Keep this index accurate.
