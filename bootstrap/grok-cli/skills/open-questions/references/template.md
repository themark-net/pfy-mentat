# Open Questions templates

## Central log: `docs/OPEN_QUESTIONS.md`

```markdown
# Open Questions

**Purpose:** Central index of open questions, TBDs, and parked decisions for multithreaded work.
Agents: scan this file at the start of multi-step work. Promote architectural answers via the ADR skill.

**Status values:** open | blocked | tbd | answered | promoted-to-adr | wont-do  
**Priority:** P0 (blocks MVP) | P1 (next milestone) | P2 | P3 (someday)

## Index

| ID | Priority | Status | Title | Blocks | Related |
|----|----------|--------|-------|--------|---------|
| OQ-0001 | P0 | open | Example title | MVP smoke | Decision 0010, pkg/foo.py |

## Detail

### OQ-0001: Example title

- **Priority:** P0
- **Status:** open
- **Created:** YYYY-MM-DD
- **Updated:** YYYY-MM-DD
- **Blocks:** MVP smoke path
- **Blocked-by:** —
- **Related-ADR:** —
- **Related-code:** `path/to/file.py`
- **Feature/runbook:** mvp-closed-loop

**Question:** Clear question that needs an answer.

**Context:** Why this matters; what we already know.

**Options:**
1. …
2. …

**Recommendation:** (optional)

**Resolution notes:**
- (append dated notes; never delete)
```

## Detail file (optional): `docs/open-questions/OQ-NNNN-slug.md`

Use the same detail body as above. Central log keeps only the index row; detail file holds the rest. Link from the title cell: `[title](open-questions/OQ-NNNN-slug.md)`.
