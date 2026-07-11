---
name: adr
description: >
  Architecture Decision Resource (ADR) skill: locate or create a project ADR
  log, read it before design work, and record decisions with context, rationale,
  rejected alternatives, and consequences so choices are not re-litigated.
  Use when the user runs /adr, asks to record or log an architecture decision,
  write an ADR, supersede a prior decision, or when a non-trivial design choice
  needs a durable decision entry. Portable across any git project.
argument-hint: "[propose|accept|supersede|list] [title or ID]"
---

# ADR — Architecture Decision Resource

You enforce a documented decision process. Filesystem ADRs in the **active repo** are the source of truth (reviewable in PRs). Never invent a second parallel decision system in a repo that already has one.

## When to run

- User invokes `/adr` or asks to log / record / supersede a decision.
- Before implementing a non-trivial design change that would re-open settled architecture.
- When promoting an answered Open Question that is architectural (see `/open-questions`).

## Step 0 — Resolve project root and ADR store

1. Find the git root of the active project (`git rev-parse --show-toplevel`). Work only inside that tree for on-disk artifacts.
2. **Locate the existing ADR store** (first match wins; do not fork):
   1. `docs/DECISIONS.md` — single-file log (common; e.g. gom-jobbar)
   2. `docs/ADR.md` or `docs/adrs.md`
   3. `docs/adr/README.md` + `docs/adr/NNNN-*.md` files
   4. `ARCHITECTURE_DECISIONS.md` at repo root
3. If **none** exist: create the **preferred new-project layout**:
   - `docs/adr/README.md` (index table)
   - `docs/adr/0001-<slug>.md` for the first decision (or a process bootstrap decision)
4. Also locate architecture doc if present: `docs/ARCHITECTURE.md`, `ARCHITECTURE.md`, or equivalent. Read ADR store + architecture **before** writing a new decision that might conflict.

**Rule:** If `docs/DECISIONS.md` already exists, **append** there. Do **not** create `docs/adr/` alongside it unless a new Accepted decision explicitly migrates the store.

## Step 1 — Modes

| Mode | Behavior |
|------|----------|
| `list` | Summarize decisions: ID, title, status. Flag Superseded. |
| `propose` | Draft a full entry with Status: Proposed; do not mark Accepted without user OK on contentious choices. |
| `accept` (default when logging a settled choice) | Write Status: Accepted (or update Proposed → Accepted). |
| `supersede <old-id>` | Write new decision; set old Status to `Superseded by <new-id>`; link both ways. |

If the user only states a decision in chat, treat as `accept` after confirming the text is accurate.

## Step 2 — Numbering

- Scan all existing IDs (`Decision 0001`, `ADR-0001`, `0001-slug.md`, etc.).
- Next ID = max + 1, zero-padded to 4 digits. **Never reuse** numbers (skipped numbers are fine).
- Slug: lowercase kebab-case short title for multi-file layout.

## Step 3 — Write the entry

Use the template in `references/template.md` (same directory as this skill). Required fields:

- **Status:** `Proposed` | `Accepted` | `Rejected` | `Superseded by NNNN`
- **Context:** situation that forced a choice
- **Decision:** precise statement of what was chosen
- **Rationale:** why; include **1–3 rejected alternatives** with concrete reasons
- **Consequences:** positive outcomes + constraints; what is now required or forbidden
- **References:** code paths, commits, related OQ IDs, architecture sections

**Single-file log:** append a new `## Decision NNNN: Title (YYYY-MM-DD)` section at the bottom (before any trailing "How to Add" boilerplate if present; keep that section last).

**Multi-file layout:** write `docs/adr/NNNN-slug.md` and add a row to `docs/adr/README.md` index.

## Step 4 — After write

1. If superseding: update the old entry's Status and add a forward link.
2. Grep the repo for comments that re-argue the old choice (`TODO decide`, obsolete "stub" claims). Point them at the new decision ID when clearly related.
3. If the decision changes layering or system boundaries, update `docs/ARCHITECTURE.md` (or run `/docs` architecture path) in the **same** change set.
4. Optional MCP mirror: if `codebase-memory` has this project indexed and `manage_adr` is available, update with a short summary. **Filesystem remains source of truth.**

## Step 5 — Report to user

- Path(s) written
- Decision ID and one-line summary
- Whether anything was superseded
- Reminder: agents must re-read the ADR log before re-proposing rejected designs

## Anti-patterns

- Creating `docs/adr/` when `docs/DECISIONS.md` already holds history
- Accepting a decision with no rejected alternatives (weak rationale)
- Silently changing Status without a superseding entry when overturning Accepted work
- Putting secrets (API keys, passwords) in ADR text
- Writing ADRs only in chat without a repo file

## Process depth

Full process rules: `references/process.md`.
