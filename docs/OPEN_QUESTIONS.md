# Open Questions

**Purpose:** Central index of open questions, TBDs, and parked decisions for multithreaded work.  
Agents: scan this file at the start of multi-step work. Promote architectural answers via `/adr`.

**Promotion rule:** Do **not** open an OQ for optional tools with a safe default (skip install / pin only). Use catalog I1 + priority instead. See [ops/human-decision-inventory.md](ops/human-decision-inventory.md) § “When to open an OQ”. (Lesson: OQ-0007 Antigravity.)

## GitHub issues (synced 2026-07-30)

| OQ | Issue | Status |
|----|-------|--------|
| OQ-0003 | [#17](https://github.com/themark-net/pfy-mentat/issues/17) | **answered** (wait + integration stages) |
| OQ-0004 | [#18](https://github.com/themark-net/pfy-mentat/issues/18) | **answered** (submodule later; still in dev) |
| OQ-0007 | [#19](https://github.com/themark-net/pfy-mentat/issues/19) | **answered** (skip; low-pri eval) |
| OQ-0008 | [#20](https://github.com/themark-net/pfy-mentat/issues/20) | **answered** (250GB pool + golden-tasks) |
| **OQ-BATCH** | [#29](https://github.com/themark-net/pfy-mentat/issues/29) | **closed** 4/4 |

## Qualification model

| Field | Values | Meaning |
|-------|--------|---------|
| **Priority** | `P0` / `P1` / `P2` / `P3` | Same scale as TODO: P0 blocks critical path |
| **Status** | `open` \| `blocked` \| `tbd` \| `answered` \| `promoted-to-adr` \| `wont-do` | `tbd` = parked with enough context for another agent; `open` = needs attention |
| **Blocks** | workstream or T-IDs | What cannot finish until this is resolved |
| **Related** | ADR, code paths, T-IDs | Graph edges |

**In-context rule:** When a question arises in code or docs, add a central row (and optional `docs/open-questions/OQ-NNNN-slug.md`) **or** a local note citing **`OQ-NNNN`**. Never leave P0–P2 only in chat. Prefer catalog I1 + default over OQ when reversible.

Related work queue: [TODO.md](TODO.md)

---

## Index (active + recent)

| ID | Priority | Status | Title | Blocks | Related |
|----|----------|--------|-------|--------|---------|
| [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | **P1** | answered | Eval harness = tier0 smokes + tier1 scored task (opt 5); DSPy later | — | ADR-0002; T-0003 |
| [OQ-0005](open-questions/OQ-0005-grok-in-cage-strategy.md) | **P1** | answered | Dual path: host-Grok default + optional grok-in-image (T-0022) | — | ADR-0002; overlays/grok |
| [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | **P1** | promoted-to-adr | Skill port strategy: hybrid first-party + paths snapshots | — | [ADR-0009](adr/0009-skill-port-hybrid-strategy.md) |
| [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | P2 | **answered** | Wait — no first embed; integration stages I0–I4 | — | [#17](https://github.com/themark-net/pfy-mentat/issues/17) |
| [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | P2 | **answered** | ATG submodule later (still in dev); I1 now | — | [#18](https://github.com/themark-net/pfy-mentat/issues/18) · [#30](https://github.com/themark-net/pfy-mentat/issues/30) |
| [OQ-0007](open-questions/OQ-0007-antigravity-need.md) | P2 | **answered** | Skip Antigravity; low-pri catalog eval | — | [#19](https://github.com/themark-net/pfy-mentat/issues/19) |
| [OQ-0008](open-questions/OQ-0008-colibri-weights-ok.md) | P2 | **answered** | 250GB model pool + golden-task proximity eval | — | [#20](https://github.com/themark-net/pfy-mentat/issues/20) · [local-model-storage-and-eval.md](ops/local-model-storage-and-eval.md) |
| [OQ-0009](open-questions/OQ-0009-write-guard-default-mode.md) | P1 | answered | Default WRITE_GUARD_MODE for new envs (audit vs enforce) | T-0031 | ADR-0007; default **audit** |
| [OQ-0001](open-questions/OQ-0001-seed-x-post-content.md) | P3 | answered | Seed X post content extraction | — | Superseded by Entries 001–010 processed |
| [OQ-0010](open-questions/OQ-0010-voice-agent-channel.md) | P2 | **resolved** | Voice half-duplex local-first (not cloud duplex) | T-0091 | [ADR-0012](adr/0012-voice-half-duplex-local-first.md) |

---

## Needs operator input soon (P1)

*No open P0/P1/P2 OQs.* 2026-07-30 batch complete.

Recently closed:

1. ~~**OQ-0005** — Grok in-cage~~ → dual path.  
2. ~~**OQ-0006** — Skill port~~ → ADR-0009.  
3. ~~**OQ-0002** — Eval harness~~ → option 5.  
4. ~~**OQ-0009** — Write-guard default~~ → audit.  
5. ~~**OQ-0003** — First subtree~~ → wait + integration stages.  
6. ~~**OQ-0004** — ATG~~ → submodule later.  
7. ~~**OQ-0007** — Antigravity~~ → skip; OQ promotion fix.  
8. ~~**OQ-0008** — Weights / models~~ → 250GB pool + golden-tasks.

## Hygiene

- Re-scan this table when starting a milestone; close or re-prioritize stale P0/P1s.
- When answering: append dated **Resolution notes** in the detail file; set Status; promote architecture to `/adr`; close linked GitHub issue.
- Before creating a new OQ: check “When to open an OQ” in human-decision-inventory.
