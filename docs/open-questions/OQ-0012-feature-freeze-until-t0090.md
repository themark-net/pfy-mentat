# OQ-0012: Feature freeze on new levers until T-0090 (≤3 levers) is actually done?

- **Priority:** **P0**
- **Status:** **open** (needs owner; 2026-09-20)
- **Blocks:** intake of new `./pfy` verbs / lanes / decision layers / attach modes
- **Related:** [critical-review-2026-09-20.md](../ops/critical-review-2026-09-20.md) §1.1, §4.1 · T-0090 · [#1](https://github.com/themark-net/pfy-mentat/issues/1) · OQ-0011 · [product-operator-surface.md](../ops/product-operator-surface.md)

## Question

**Question:** Should new lever/feature intake into `./pfy` stop until the end-user surface is measurably ≤3 levers (T-0090), and what is the exception rule?

T-0090 (“collapse end-user surface to onboard / stage / ship; ≤3 levers”) is the only P0 in `docs/TODO.md`. GitHub #1 was closed *COMPLETED* on 2026-07-30 because the **Make** surface met “≤5 product targets”. Since then the **`./pfy`** surface grew from 7 verbs (ADR-0012) to 21 top-level + ~24 sub-verbs via ~20 P1 features (attach modes, orchestration, code-graph, OpenContext, recommend/try, catalog ask/queue, live org queue, Codex/Claude attach, launch wizard, session compose, Gab lane, Jev decision layer).

**Should new lever/feature intake stop until the surface is measurably ≤3 levers?**

## Options

### Option A — Yes: hard freeze

- No new `./pfy` verbs, board routes, GUI tabs, lanes, or decision layers until `./pfy help` lists ≤3 product levers (+ `status`, `help`, and an `advanced`/`lab` escape hatch).
- **Exception rule:** a new verb is allowed only if it *replaces* ≥2 existing ones (net negative) or is a bug fix to an existing verb. Anything else goes to `examples/` behind `PFY_EXPERIMENTAL=1`.
- T-0090 is reopened on GitHub (or a new issue) with the measurable DoD: `./pfy help | grep -c '^  pfy '` ≤ 5.
- Consequence: momentum stops for one consolidation pass; the product becomes explainable.

### Option B — Soft freeze

- New features allowed only under `PFY_EXPERIMENTAL=1` and only in `examples/`; the product `./pfy help` is frozen at today’s list and shrinks over time.
- Same DoD for T-0090, no deadline.
- Consequence: slower collapse; less friction.

### Option C — No freeze; drop G8 “≤3 levers”

- Rewrite DESIGN G8 and `product-operator-surface.md` to say the operator surface is a **power-user CLI** with grouped verbs (`pfy models …`, `pfy launch …`).
- Requires an ADR superseding the “≤3 levers” language of ADR-0012.
- Consequence: honest, but abandons the simplicity thesis that justified the product in the first place.

## Interaction with OQ-0011

If OQ-0011 → A (catalog primary) or C (framework primary), Option A here is nearly free.  
If OQ-0011 → B (operator stack primary), the owner must still pick A/B/C here, because B without a freeze is the status quo that produced §1.1.

## What the owner needs to answer

1. A / B / C.
2. The exception rule text (Option A proposes “net-negative verbs only”).
3. Who measures: proposal is the G0 structural lane counts `./pfy help` product verbs and FAILs above the cap once T-0090 is re-opened.

## Resolution notes

*(pending)*
