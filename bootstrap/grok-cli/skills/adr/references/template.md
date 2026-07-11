# ADR entry template

Copy into the project ADR store. Replace placeholders.

## Single-file form (`docs/DECISIONS.md`)

```markdown
## Decision NNNN: Short Descriptive Title (YYYY-MM-DD)

**Status:** Proposed | Accepted | Rejected | Superseded by NNNN

**Context:** One or two paragraphs describing the situation or question that forced a decision.

**Decision:** Precise statement of what was chosen.

**Rationale:** Why this option. Explicitly call out the strongest 1–3 rejected alternatives and the concrete reasons they were set aside (complexity, existing contracts, time-to-value, safety, alignment with sibling systems, etc.).

**Consequences:** Positive outcomes and ongoing constraints. What future work is now required or forbidden.

**References:** Paths (`pkg/module.py:line`), commits, related OQ-NNNN, architecture sections, external docs.
```

## Multi-file form (`docs/adr/NNNN-slug.md`)

```markdown
# ADR-NNNN: Short Descriptive Title

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Rejected | Superseded by ADR-MMMM
- **Deciders:** (optional)

## Context

## Decision

## Rationale

Rejected alternatives:
1. …
2. …

## Consequences

## References
```

## Index row (`docs/adr/README.md`)

```markdown
| ID | Title | Status | Date |
|----|-------|--------|------|
| 0001 | Short title | Accepted | YYYY-MM-DD |
```
