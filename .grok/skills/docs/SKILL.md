---
name: docs
description: >
  Documentation skill: ensure generated or changed code gets human operator
  docs (how it works, where variables live, how to run) plus an agent section
  (structural map, invariants, ADR links) tied back to architecture. Use when
  the user runs /docs, asks for operator docs, module docs, "how does this
  work", "where do variables live", or after implementing non-trivial code.
  Portable across projects.
argument-hint: "[module|architecture|runbook|audit] [path or name]"
---

# Docs — Operator + Agent Documentation

You leave documentation that a human can operate and an agent can navigate structurally, always linked to the project's architecture map.

## When to run

- User invokes `/docs`.
- After adding or substantially changing a module, CLI surface, integration, or public API.
- Architecture or status docs drift from code (audit mode).
- New operator runbook needed (MVP path, deploy, recovery).

## Step 0 — Resolve layout

Git root. Prefer existing docs layout; otherwise create:

```
docs/
  ARCHITECTURE.md       # system map (or update existing equivalent)
  modules/<name>.md     # per major module/package area
  ops/<runbook>.md      # operator closed-loops
```

Also respect project conventions (e.g. `AGENTS.md` pointers). Search for existing architecture filenames before creating a second map.

## Step 1 — Modes

| Mode | Behavior |
|------|----------|
| `module <path-or-name>` | Write/update `docs/modules/<name>.md` from code |
| `architecture` | Refresh system map: layers, data flow, delivered vs future |
| `runbook <name>` | Operator closed-loop under `docs/ops/` |
| `audit` | Diff code vs docs; list stale claims; fix critical falsehoods |

## Step 2 — Module doc requirements

Every module doc **must** include:

### Human operator

- What it does (plain language)
- How to run (CLI, UI, scripts)
- Failure modes and recovery
- **Configuration / variables table:** name, where defined (env, config file, constant), purpose

### Agent

- Entry points (functions/classes, CLI verbs)
- Data shapes (key types, JSON blobs, DB tables)
- Callers / callees (structural; use codebase-memory graph tools if the project is indexed, else grep)
- Invariants + **ADR / Decision IDs**
- Extension points
- **Do not** (forbidden changes; sacred data rules)

### Architecture link

- Which layer of `docs/ARCHITECTURE.md` this module sits in
- If the change moves a boundary, update ARCHITECTURE in the **same** change set

Template: `references/module-template.md`. Architecture checklist: `references/architecture-checklist.md`.

## Step 3 — Code-to-docs discipline

When you generate non-trivial code in a session:

1. Identify the owning module(s).
2. Create or update the module doc.
3. If public CLI/env surface changed → update operator section + runbook if any.
4. If layering changed → architecture.
5. If a binding design choice was made → remind or run `/adr`.
6. If a parked question remains → `/open-questions`.

Do not claim "docs later" for P0 operator paths.

## Step 4 — Quality bar

- No secrets in docs (use placeholders).
- Prefer tables for env vars and CLI verbs.
- Stale "future" claims about already-shipped features are bugs — fix on audit.
- Agent sections are structural, not essays; link ADRs instead of re-arguing them.

## Step 5 — Report

- Paths written/updated
- Modules covered
- Architecture changes (if any)
- Remaining doc debt as OQ suggestions if large

## Anti-patterns

- Docs that only restate the README marketing blurb
- Operator docs without env/config locations
- Agent docs with no entry points or invariants
- Second architecture file that contradicts the first
