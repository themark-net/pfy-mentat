# Architecture Decision Records (ADR) — {{PROJECT_NAME}}

**Store layout:** multi-file under `docs/adr/`.  
**Process:** Grok skill `/adr` (or project-process skill if skills not installed).

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [0001](0001-process-docs-bootstrap.md) | Process docs bootstrap (DESIGN/ADR/TODO/OQ) | Accepted | {{DATE}} |

## How to add

1. Next free `NNNN` (never reuse).
2. Create `docs/adr/NNNN-slug.md` with Context, Decision, Rationale (**rejected alternatives**), Consequences, References.
3. Add a row to this index.
4. If layering changes, update `docs/ARCHITECTURE.md` and DESIGN in the same change set.
5. Link related OQs; promote answered architectural OQs here.

## Lifecycle

`Proposed` → `Accepted` | `Rejected`  
`Accepted` → `Superseded by NNNN` (new entry required; never silent overwrite)
