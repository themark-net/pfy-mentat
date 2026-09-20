# ADR-0017: Product = catalog + evaluation + local handoff harness (toolset × harness, hedged lanes)

- **Status:** Accepted
- **Date:** 2026-09-20
- **Deciders:** owner (answer to [OQ-0011](../open-questions/OQ-0011-product-primacy.md)); agent (write-up)
- **Related:** [ADR-0011](0011-hybrid-operator-surfaces-grok-opencode-ollama.md) (surfaces) · [ADR-0012 launch](0012-simple-harness-agnostic-launch.md) (G8) · [ADR-0014](0014-pluggable-local-inference-spine.md) · [ADR-0015](0015-catalog-json-slim-subset.md) · [ADR-0016](0016-jev-decision-layer.md) · [critical-review-2026-09-20.md](../ops/critical-review-2026-09-20.md) · OQ-0012 · OQ-0013
- **Resolves:** OQ-0011 (product primacy); forces the layout answer for OQ-0013

## Context

The 2026-09-20 critical review found that the repo held three candidate products (scored catalog, `./pfy` operator stack, process framework) and behaved as if none were primary: the catalog was frozen ("HOLD 70–75"), the operator surface grew from 7 to 21 verbs, and the only P0 (T-0090 ≤3 levers) was contradicted by GitHub. [OQ-0011](../open-questions/OQ-0011-product-primacy.md) asked the owner to pick A (catalog), B (operator stack), C (process framework) or D (status quo).

The owner answered on 2026-09-20 (verbatim):

> "the product is catalog, evaluation, local handoff harness. implement valuable tools from catalog, allow local/remote handoff to any harness, any toolset. the toolset for example, newest is jev, should be 'implementable' with whatever harnesses we're wiring. the local/cloud handoff should allow 'hedging' cloud credits with local compute. the point is a catalog with an implementation not one or the other."

Facts that constrain the design (all verifiable in the tree at this commit):

- Toolsets are hard-wired per harness today. `scripts/pfy_attach_usable_{196,202,220,221}.py` are 84–91 % identical clones; each applies the same `_apply_opencontext_env` / `_apply_attach_mode_env` chain and differs only in the binary name. `pfy_code_graph_215.prepare()` branches on `hid in ("opencode","grok")` vs `("hermes","codex","claude")` inline. Jev (`pfy_jev_230.py`) is applied only as a pre-launch gate in the wizard; no harness receives a Jev brief or config.
- Harness config surfaces already exist and are already used: `GROK_HOME/skills` + `GROK_HOME/config.toml` (`[mcp_servers.*]`, merged by `bootstrap/grok-cli/scripts/merge_config.py`); `$PFY_STATE_DIR/opencode.json` (`mcp` map) + `OPENCODE_SKILLS`; env + `PFY_ATTACH_AGENTS` / `PFY_SESSION_BRIEF` prompt cards for Claude / Codex / Hermes.
- Lanes are named but not budgeted. `docs/ops/local-cloud-split.md` has a routing heuristic ("bulk → local worker; hard → Grok monitor") with no ledger, no budget input, and no deterministic decision function; `DEPLOY_PROFILE` gates cloud only as an on/off switch.
- The catalog knows nothing about implementations. `data/tools.json` rows have `integration_stage` (I0–I4) but no pointer to the code that implements them; a toolset cannot be traced back to its catalog row.

## Decision

1. **The product is a triad, not one of three.** pfy-mentat ships (1) the **scored catalog** (`TOOLS.md` + slim `data/tools.json`, ADR-0015), (2) **evaluation** (structural / golden / model lanes under `examples/eval-harness/`), and (3) a **local handoff harness** that takes a *toolset* and applies it to *any wired harness* on a *local or cloud lane*. None is "how we choose pieces" for the others; each is a deliverable with its own gate.
2. **Toolsets and harnesses are orthogonal axes.** A toolset is declared **once** in `data/toolsets.json` (`id`, `catalog_tool`, `provides` = env / MCP servers / prompt brief / commands, `lanes`, and a per-harness `implementation` cell). Harnesses stay in `data/harnesses.json`. The product surface for this is the **matrix**: every toolset × every `role: harness` slot has exactly one honest cell `implemented | partial | stub` with a `how` string. Statuses are derived from what the code does today, never from intent.
3. **A toolset is applied through a plan.** `plan(toolset, harness, lane)` returns a concrete apply plan (env dict, files to write, MCP fragments, brief text) or an honest `stub` result with a next step. `apply` writes only under `$PFY_STATE_DIR` or the harness's own config dir, and only with `--yes`. Jev (ADR-0016) is the **reference toolset**: implemented for the harnesses whose config surfaces already exist in the repo (Grok, OpenCode, Claude Code, Codex), partial for Hermes, stub elsewhere.
4. **Lanes are hedged, not toggled.** A deterministic **hedge policy** (`pfylib/hedge.py`) decides `local | cloud` from task class (`bulk | hard | interactive`), local engine availability (ADR-0014 detector), and a cloud credit budget (`PFY_CLOUD_BUDGET`) with a ledger at `$PFY_STATE_DIR/hedge-ledger.json`. Local first, always; cloud only when local is missing or the task is `hard`, **and** budget remains; neither → `FAIL` with a next step, never a fake lane.
5. **Catalog rows and implementations link both ways.** A `data/tools.json` row that has an implementation carries `implementation: {"toolset": <id>, "stage": "I0–I4"}`; the toolset's `catalog_tool` names the row. `scripts/catalog_check.py` validates the link. A toolset with no catalog row says `catalog_tool: null` — we do not invent rows or scores to close the loop.
6. **The catalog HOLD (70–75) is lifted as a policy.** "Catalog 70–75 HOLD · do not reopen #76 · #198 parked" stops being copied into prompt strings, briefs and selftests. Whether the specific entries 070–075 are accepted, re-scored or rejected is ordinary catalog work (T-0123), not a standing instruction to agents. Closed issues are not reopened by anyone; that does not need a liturgy.

### How this refines earlier ADRs (nothing is superseded outright)

| ADR | Before | After this ADR |
|-----|--------|----------------|
| [ADR-0011](0011-hybrid-operator-surfaces-grok-opencode-ollama.md) | Grok = primary/monitor surface, OpenCode = secondary/worker; routing is a **heuristic table** | Surfaces unchanged. Routing becomes a **deterministic, budgeted hedge** (`./pfy hedge decide`). "Grok primary" means *default harness*, not *default lane*: the lane is decided by hedge, the harness by the operator. |
| [ADR-0012 launch](0012-simple-harness-agnostic-launch.md) | G8: one launcher, harness registry, honest stubs, ≤3 product levers | Registry unchanged and now paired with a **toolset registry**. The lever count is still measured on `./pfy help` (T-0090). This ADR adds two verbs (`toolset`, `hedge`) and **records that as a tension**, not a resolution — OQ-0012 (feature freeze) decides how the surface shrinks; candidates for collapse are the per-toolset verbs (`decision`, `code-graph`, `context`, `catalog ask`) that `toolset plan/apply` generalises. |
| [ADR-0015](0015-catalog-json-slim-subset.md) | `data/tools.json` is a slim machine subset of `TOOLS.md` | Still slim. A row is *also* added when a toolset implements it (so the link in (5) can exist); scores are copied from `TOOLS.md`, never invented. |
| [ADR-0016](0016-jev-decision-layer.md) | Jev = decision layer toggled in the wizard; "Catalog 70–75 stay HOLD. Do not reopen #76." | Jev = the **reference toolset** in the matrix; the HOLD sentence is retired by (6). Paths, confidence gate and honesty chips unchanged. |

## Rejected alternatives

| Option | Why not |
|--------|---------|
| **A — Catalog only is primary** (OQ-0011 A) | Recovers the differentiated asset but abandons the owner's stated need: a catalog whose "valuable" rows have **implementations**. A scores-only catalog cannot show that Jev runs on OpenCode. The owner: "a catalog with an implementation not one or the other". |
| **B — Operator stack / GUI is primary** (OQ-0011 B) | Locks the product to one operator's box (nimo, FreeToken :1919, Grok subscription, Gab lane). The review showed a clean box yields "a well-behaved status printer with ~45 verbs and no runnable session". Nothing in the owner's answer names the window, Tauri, voice or the board; they become **optional lab**, not the path. |
| **C — Process framework is primary** (OQ-0011 C) | Most portable, smallest surface, but the framework is *how we work*, not *what we ship*; the owner's answer does not mention it. It stays mandatory process (ADR-0001/0005), not product. |
| **D — Status quo, all three co-equal** (OQ-0011 D) | Rejected by the review as the cause of the §1.1 contradictions (HOLD vs "living", ≤3 levers vs 21 verbs, "local first" vs cloud default). Co-equal *without* a linking mechanism is what we had; the triad here is linked by (2) and (5). |
| **One toolset hard-wired per harness** (current `attach_usable_*` clones, `code_graph_215.prepare()` branches) | O(toolsets × harnesses) copies of the same env/brief logic; each new harness re-implements every toolset and each new toolset patches every harness. 91 % duplication already; no unit tests possible because modules import each other by file path. Rejected in favour of one declaration + one plan function per toolset. |
| **Cloud/local as a profile switch only** (`DEPLOY_PROFILE=local-only|balanced|max-performance`) | A profile cannot "hedge": it cannot say "local for this bulk task, cloud for this hard one, and stop at N credits". Profiles stay as defaults the hedge reads; the per-task decision needs a function and a ledger. |
| **Hedge by measured latency/quality** | Requires live probes and per-model quality data we do not have offline; not deterministic; would fail on the clean box. Chosen: a rule-based policy over three observable inputs, testable without a network. Revisit when the eval lane produces per-model quality receipts. |
| **`pfy/` as the package name** | The repo root already has an executable file named `pfy`; a directory `pfy/` and a file `pfy` cannot coexist. Package is **`pfylib/`**; `./pfy` stays the user-facing name. |
| **Port `scripts/pfy` (bash) to Python in this change** | Would churn 1,900 lines of launcher whose `help/status/harness list` output is baseline-pinned; not needed for the matrix. The bash stays a thin dispatcher for the new verbs (OQ-0013 option A); wholesale port is T-0121's call. |

## Consequences

- **Package layout (engineering consequence for OQ-0013):** `pfylib/` at repo root — `registry.py` (loads `data/harnesses.json` + `data/toolsets.json`), `toolsets.py` (`matrix()`, `plan()`, `apply()`; Jev reference implementation reusing `scripts/pfy_jev_230.py` by import, not copy), `hedge.py`, `cli.py`; `tests/` (stdlib `unittest`, run via `python3 -m unittest discover -s tests`) wired into `run_structural.py` and `eval-structural.yml`. Modules are named by concept; issue numbers live in docstrings. Remaining `scripts/pfy_*_NNN.py` migrate onto `pfylib/` incrementally (T-0121). OQ-0013 is marked `promoted-to-adr` with this file; the owner may still veto the layout.
- **`./pfy toolset list | matrix | plan | apply` and `./pfy hedge decide | ledger`** exist as thin `exec python3 pfylib/cli.py` verbs. This is **+2 top-level verbs** against T-0090's "fewer"; the tension is recorded here and left to OQ-0012.
- **GUI / voice / Space Invaders / Tauri** are **optional lab**, not the product path. They are not deleted by this ADR; they are no longer what README leads with. A keep-or-park decision per lab item is ordinary TODO work.
- **T-0090 is measured on `./pfy help`** verb count, as the review demanded; not on Make targets.
- **Catalog HOLD lifted** (T-0123): resume receipts, decide entries 070–075 on their merits, add `implementation` to rows that have one.
- **New eval lane:** the toolset × harness matrix is a structural check — every cell present, status valid, `implemented` cells produce non-empty env/brief in tests. Later: a live lane that applies a plan and proves the harness saw it (needs binaries; owner's box or cage).
- **Hedge ledger** is append-only JSON under `$PFY_STATE_DIR`; live spend tracking from real harness runs is T-0122. Budget unit is **credits** as an integer the operator defines (default 0 = no cloud spend allowed unless local is missing; see `docs/modules/pfylib.md`).
- **Harness registry column disagreement** (`./pfy status` live vs `harness list` static) is unchanged here; the matrix column is explicitly `IMPLEMENTATION`, not `STATUS`, to avoid a third meaning.

## References

- `data/toolsets.json` · `pfylib/` · `tests/`
- [docs/modules/pfylib.md](../modules/pfylib.md)
- [docs/ops/critical-review-2026-09-20.md](../ops/critical-review-2026-09-20.md) §1, §6
- [docs/ops/integration-stages.md](../ops/integration-stages.md) (I0–I4 used by `implementation.stage`)
- [docs/ops/local-cloud-split.md](../ops/local-cloud-split.md) (heuristic the hedge replaces)
