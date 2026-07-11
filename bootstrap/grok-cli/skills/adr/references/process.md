# ADR process rules

## When a decision is required

Write an ADR when the choice is:

- Hard to reverse (schema, public CLI, data ownership, security posture)
- Likely to be re-debated by a future agent or human
- Choosing among real alternatives (not pure mechanical cleanup)
- Superseding or relaxing a prior Accepted decision

Skip formal ADRs for:

- Pure renames, formatting, dependency bumps with no behavioral change
- Local-only experiments behind a throwaway branch (until they land on main)

## Lifecycle

```
Proposed ──► Accepted
    │            │
    │            ├──► Superseded by NNNN (context changed; new entry required)
    │            └──► (stays Accepted forever if still true)
    └──► Rejected (explicitly not chosen; keep for anti-pattern memory)
```

- **Proposed:** draft for user review; do not treat as binding until Accepted.
- **Accepted:** binding for agents; re-implementation of rejected alternatives needs a superseding ADR.
- **Superseded:** old entry stays for history; Status must name the new ID.
- **Rejected:** used when logging a considered-and-declined path without accepting a different full design (rare; prefer Accepted of the chosen path with rejected alternatives inside Rationale).

## Supersede checklist

1. New entry explains **what context changed** (why the old decision no longer holds).
2. Old entry Status → `Superseded by NNNN`.
3. New entry References → old ID.
4. Code/docs that cited the old decision are updated or dual-cited.

## Relationship to Open Questions

- Open Questions hold TBDs and priorities; ADRs hold settled architecture.
- When an OQ is architectural and answered → promote via `/adr`, set OQ status `promoted-to-adr`.

## Relationship to Docs skill

- ADR records *why*. Module docs record *how* and *where*.
- Architecture doc records *current shape*. Update it when an Accepted decision changes layering.

## Cross-project portability

This skill never hardcodes a product name. Only search-order paths and templates are fixed. Project-specific process notes belong in that project's `AGENTS.md` or a Decision that defines local conventions (e.g. "we keep a single DECISIONS.md").
