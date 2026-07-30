# Open Questions

**Purpose:** Central index of open questions, TBDs, and parked decisions for multithreaded work.  
Agents: scan this file at the start of multi-step work. Promote architectural answers via `/adr`.

## GitHub issues (synced 2026-07-30)

| OQ | Issue | Status |
|----|-------|--------|
| OQ-0003 | [#17](https://github.com/themark-net/pfy-mentat/issues/17) | **answered** (wait + integration stages) |
| OQ-0004 | [#18](https://github.com/themark-net/pfy-mentat/issues/18) | open |
| OQ-0007 | [#19](https://github.com/themark-net/pfy-mentat/issues/19) | tbd |
| OQ-0008 | [#20](https://github.com/themark-net/pfy-mentat/issues/20) | tbd |
| **OQ-BATCH** | [#29](https://github.com/themark-net/pfy-mentat/issues/29) | 1/4 done; remaining 0004, 0007, 0008 |

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
| [OQ-0002](open-questions/OQ-0002-eval-harness-shape.md) | **P1** | answered | Eval harness = tier0 smokes + tier1 scored task (opt 5); DSPy later | — | ADR-0002; T-0003 |
| [OQ-0005](open-questions/OQ-0005-grok-in-cage-strategy.md) | **P1** | answered | Dual path: host-Grok default + optional grok-in-image (T-0022) | — | ADR-0002; overlays/grok |
| [OQ-0006](open-questions/OQ-0006-skill-port-strategy.md) | **P1** | promoted-to-adr | Skill port strategy: hybrid first-party + paths snapshots | — | [ADR-0009](adr/0009-skill-port-hybrid-strategy.md) |
| [OQ-0003](open-questions/OQ-0003-first-subtree-candidate.md) | P2 | **answered** | Wait — no first embed; integration stages I0–I4 | — | [#17](https://github.com/themark-net/pfy-mentat/issues/17) · [integration-stages.md](ops/integration-stages.md) |
| [OQ-0004](open-questions/OQ-0004-atg-prototype-relationship.md) | P2 | open | How ATG prototype relates to this catalog | T-0004 | [#18](https://github.com/themark-net/pfy-mentat/issues/18) · atg-framework, TOOLS.md |
| [OQ-0007](open-questions/OQ-0007-antigravity-need.md) | P2 | tbd | Do we need Antigravity-Manager multi-account relay? | T-0015 | [#19](https://github.com/themark-net/pfy-mentat/issues/19) · LiteLLM |
| [OQ-0008](open-questions/OQ-0008-colibri-weights-ok.md) | P2 | tbd | OK to download colibri model weights on this machine? | T-0016 | [#20](https://github.com/themark-net/pfy-mentat/issues/20) · disk/RAM |
| [OQ-0009](open-questions/OQ-0009-write-guard-default-mode.md) | P1 | answered | Default WRITE_GUARD_MODE for new envs (audit vs enforce) | T-0031 | ADR-0007; default **audit** |
| [OQ-0001](open-questions/OQ-0001-seed-x-post-content.md) | P3 | answered | Seed X post content extraction | — | Superseded by Entries 001–010 processed |
| [OQ-0010](open-questions/OQ-0010-voice-agent-channel.md) | P2 | **resolved** | Voice half-duplex local-first (not cloud duplex) | T-0091 | [ADR-0012](adr/0012-voice-half-duplex-local-first.md) |

---

## Needs operator input soon (P1)

*No open P1 OQs.* Remaining: OQ-0004, OQ-0007, OQ-0008 (P2).

Recently closed:

1. ~~**OQ-0005** — Grok in-cage~~ → **answered: dual path**.  
2. ~~**OQ-0006** — Skill port strategy~~ → **ADR-0009 hybrid**.  
3. ~~**OQ-0002** — Eval harness shape~~ → **option 5**.  
4. ~~**OQ-0009** — Write-guard default~~ → **answered: audit**.  
5. ~~**OQ-0003** — First subtree~~ → **answered: wait** + [integration-stages.md](ops/integration-stages.md).

## Hygiene

- Re-scan this table when starting a milestone; close or re-prioritize stale P0/P1s.
- When answering: append dated **Resolution notes** in the detail file; set Status; promote architecture to `/adr`; close linked GitHub issue.
