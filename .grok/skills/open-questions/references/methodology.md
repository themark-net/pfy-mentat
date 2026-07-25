# Open Questions methodology

## Why a central log

Parallel agents and sessions forget chat context. Code `TODO`s lack priority, ownership, and dependency edges. A single markdown log in-repo is greppable, reviewable in PRs, and requires no extra service.

## Multithreaded rules

1. **Write for the next agent.** Assume the reader has no chat history. Include paths, commands tried, and constraints.
2. **Prefer `tbd` over silent omission** when a choice can wait but must not be forgotten.
3. **P0 is sacred.** Do not ship an MVP declaration while P0 OQs remain `open` without an explicit user waiver.
4. **Graph over laundry list.** Fill Blocks / Blocked-by so critical path is visible.
5. **Promote up, don't hoard.** Architectural answers leave the OQ log as `promoted-to-adr` and live in the ADR store.

## When to use detail files vs inline

| Situation | Prefer |
|-----------|--------|
| < ~15 open items, short detail | Inline sections in `OPEN_QUESTIONS.md` |
| Long options analysis, many links, parallel workstreams | `docs/open-questions/OQ-NNNN-slug.md` |
| Runbook-attached research | Detail file + Feature/runbook field |

## Relationship to ToDos

- OQs are **decisions/questions**, not a full task board.
- Implementation tasks can reference OQ IDs in commit messages or plan todos.
- Closing an OQ does not mean the code is done; it means the **question** is resolved.

## Relationship to ADR and Docs

| Artifact | Holds |
|----------|--------|
| Open Questions | Unsettled; priorities; interconnections |
| ADR / DECISIONS | Settled architecture with rejected alternatives |
| Module / ops docs | How to operate and how code is structured |

## Hygiene

- Re-scan OQ table when starting a milestone; close or re-prioritize stale P0s.
- Quarterly (or on request): mark abandoned items `wont-do` with one-line reason.
