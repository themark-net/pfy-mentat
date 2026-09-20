# OQ-0011: Product primacy — which of the three is THE product for the next horizon?

- **Priority:** **P0**
- **Status:** **promoted-to-adr** → [ADR-0017](../adr/0017-product-catalog-evaluation-handoff-harness.md) (answered by owner 2026-09-20)
- **Blocks:** T-0090 (surface collapse), T-0111 (consolidation), OQ-0012, OQ-0013, catalog HOLD 70–75 disposition, ADR-0012 duplicate cleanup
- **Related:** [critical-review-2026-09-20.md](../ops/critical-review-2026-09-20.md) §1 · DESIGN §1 · ADR-0002 · ADR-0011 · ADR-0012 (launch) · ADR-0015

## Question

**Question:** Which of catalog / `./pfy` operator stack / process framework is THE product for the next horizon, and what budget do the other two get?

The repo contains three things that each *could* be the product:

| | What it is | Where it lives | State (2026-09-20) |
|---|---|---|---|
| **(a) Catalog** | Scored, receipt-backed catalog of local-first LLM tools (Stage 0 gate + tiers + X-post receipts) | `TOOLS.md`, `data/tools.json`, `sources/`, `CATEGORIZATION.md` | Frozen: “HOLD 70–75” since mid-Aug; last receipts 2026-07-31; PR #75 open since 2026-08-14 |
| **(b) Operator stack** | `./pfy` launcher + board + native GUI + attach lanes + model recommend + decision layer | `scripts/pfy`, `scripts/pfy-*.py`, `scripts/pfy_*_NNN.py`, `gui/` | 21 top-level verbs, ~45 total; all energy since 2026-08-25 (54 issue-tagged commits); proven only on the owner’s box |
| **(c) Process framework** | DESIGN/ADR/TODO/OQ + portable skills + `project-process` scaffold | `docs/`, `bootstrap/`, `.grok/skills/` | Working; the part other repos consume |

DESIGN §1 says (b) is the product and (a) is “how we choose pieces”. The repo’s README leads with (a). Effort goes to (b). Discipline holds in (c). **Which one is primary for the next horizon?** The other two become supporting and are held to a budget.

## Options and consequences

### Option A — Catalog is primary (the original, distinctive idea)

- Lift or formally re-scope “HOLD 70–75” via ADR; resume receipts in `sources/x-posts.md`; merge/close PR #75.
- `./pfy` shrinks to **onboard / stage / ship** (+ `status`, `help`) — the “pick a tool from the catalog and run it locally” demo, not a session manager.
- Attach lanes, Gab, Jev decision layer, launch wizard, Space Invaders, voice → `examples/` or an `experimental/` tree behind `PFY_EXPERIMENTAL=1`; keep selftests.
- Tauri GUI becomes a catalog browser or is parked.
- Consequence: throws away momentum on (b); recovers the only differentiated asset; T-0090 becomes trivially true.

### Option B — Operator stack is primary (current DESIGN §1)

- Commit to it properly: `pfy/` package, tests, one Attach implementation, an ADR for “GUI-primary” (never written), and **T-0090 measured against `./pfy help`** (≤3 levers + `status`/`help`).
- Catalog becomes an input feed only: freeze `TOOLS.md` as-is or auto-generate the browse subset from `data/tools.json`; drop the “living catalog” claim from README.
- Voice / Tauri / Space Invaders each get an explicit keep-or-park decision (a one-line ADR each).
- Consequence: honest about what the repo *is*; requires accepting the product is a personal operator box unless a second operator is on-boarded and the “works on a clean box” bar (README Stage 0 for our own product) is enforced.

### Option C — Process framework is primary

- Product = `bootstrap/project-process` + skills + the structural eval lane, shipped to other repos.
- (a) and (b) become the framework’s worked example (“dogfood repo”).
- Consequence: the smallest surface; most portable; least exciting; `./pfy` would be demoted to a dev convenience.

### Option D — Keep all three co-equal (status quo)

- Rejected by this review as the cause of §1.1 contradictions; listed for completeness. If chosen, DESIGN §1 must be rewritten to say so and G8 “≤3 levers” must be dropped or re-scoped, because it cannot be honoured while (b) grows.

## What the owner needs to answer

1. A / B / C (or D with the DESIGN rewrite).
2. For the two non-primary parts: **budget** (e.g. “catalog: ≤1 receipt batch/month”, “`./pfy`: no new verbs”).
3. Whether the “works on a clean Ubuntu/macOS box in ~5 minutes” Stage 0 bar applies to our own product surface.

## Resolution notes

**2026-09-20 — owner answer (verbatim):**

> "the product is catalog, evaluation, local handoff harness. implement valuable tools from catalog, allow local/remote handoff to any harness, any toolset. the toolset for example, newest is jev, should be 'implementable' with whatever harnesses we're wiring. the local/cloud handoff should allow 'hedging' cloud credits with local compute. the point is a catalog with an implementation not one or the other."

**Reading encoded in ADR-0017:** none of A/B/C/D as written. The product is a **triad** — (1) scored catalog, (2) evaluation, (3) a local handoff harness that applies a **toolset** (jev, gab, opencontext, code-graph, orchestration, catalog-ask, …) to **any wired harness** (grok, opencode, claude-code, codex, hermes, gemini, exo, continue) on a **local or cloud lane**, with a **hedge** policy that spends local compute first and cloud credits only when local cannot (budgeted). Toolsets × harnesses are orthogonal: declare once in `data/toolsets.json`, apply to N harnesses. Catalog rows and implementations link both ways. "Not one or the other" = the catalog HOLD (70–75) is lifted as a standing policy and rows gain an `implementation` field.

**Budgets for the non-primary parts (question 2):** GUI / voice / Tauri / Space Invaders become optional lab (not deleted, not led with). The process framework stays mandatory process, not product. No new `./pfy` verbs beyond `toolset` and `hedge` from this ADR; the surface question is OQ-0012's.

**Stage 0 bar for our own surface (question 3):** not answered by the owner; ADR-0017 keeps the review's "clean box" bar as the eval target for the matrix (`stub` is an acceptable honest cell; a fake `implemented` is not).

Promoted: [ADR-0017](../adr/0017-product-catalog-evaluation-handoff-harness.md). Work: T-0120..T-0123 in [TODO.md](../TODO.md).
