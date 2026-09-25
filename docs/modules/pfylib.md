# Module: `pfylib/` — toolset × harness handoff + hedge

**Architecture layer:** Handoff harness (product leg 3 of the triad, [ADR-0017](../adr/0017-product-catalog-evaluation-handoff-harness.md)).  
**Code:** `pfylib/` (`registry.py`, `toolsets.py`, `hedge.py`, `cli.py`, `_legacy.py`) · data `data/toolsets.json` · tests `tests/`  
**Related:** [DESIGN G9](../DESIGN.md) · [ARCHITECTURE](../ARCHITECTURE.md) · [integration-stages.md](../ops/integration-stages.md) · [local-cloud-split.md](../ops/local-cloud-split.md) · [jev-230.md](jev-230.md) · T-0120..T-0123

## Operator

### What it does

Declares each **toolset** once (`data/toolsets.json`) and applies it to any **harness** row of `data/harnesses.json` (`role == "harness"`). The matrix cell is an *implementation* status — `implemented` / `partial` / `stub` — never a live health status. `plan` turns a cell into a concrete apply plan (env exports, files, config fragments, a brief) or an honest `STUB` with a next step. `hedge` picks the lane for a task: local compute first, cloud credits only within `PFY_CLOUD_BUDGET`, `FAIL` with a next step when neither can run.

### How to run

```bash
./pfy toolset matrix                               # grid; exit 0
./pfy toolset list                                 # one line per toolset + catalog link
./pfy toolset plan jev --harness opencode          # exit 0 READY · 3 STUB · 1 FAIL
./pfy toolset plan jev --harness codex --env       # only `export K=V` lines: eval "$(...)"
./pfy toolset apply jev --harness grok             # dry-run (prints plan)
./pfy toolset apply jev --harness grok --yes       # writes GROK_HOME/skills/pfy-jev-decision/SKILL.md + brief
./pfy toolset validate                             # shape check (also run by scripts/catalog_check.py)
./pfy hedge decide --task bulk|hard|interactive    # lane=local|cloud or FAIL; --json; --record debits ledger
./pfy hedge ledger [--reset]  ·  ./pfy hedge record 3 --task hard --note "typesafe call"
python3 -m pfylib toolset matrix --json            # same entry without the bash dispatcher
python3 -m unittest discover -s tests              # offline; no runtime, no network
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | READY (plan / apply / decide succeeded, listing, dry-run of a READY plan) |
| 1 | FAIL (unknown id, lane not offered, key missing on cloud lane, hedge cannot place the task, apply refused a path) |
| 2 | usage |
| 3 | STUB — cell not wired; the output says what exists today and the next step |

### Where files go

`apply --yes` writes **only** under `$PFY_STATE_DIR` (default `~/.pfy-mentat`) or the harness's own home (`GROK_HOME`→`~/.grok`, `CODEX_HOME`→`~/.codex`, `CLAUDE_CONFIG_DIR`→`~/.claude`). Anything else is refused and reported under `failed`. Writes are idempotent: `append-marker` blocks are delimited by `<!-- pfy-toolset:<id> begin/end -->` and replaced in place; `json-merge` unions list values and updates object keys.

### Hedge units

`PFY_CLOUD_BUDGET` is an integer number of **credits** for the ledger period (operator-defined unit — dollars, calls, tokens/1k; pick one and be consistent). One cloud decision costs `PFY_CLOUD_TASK_COST` credits (default 1). Ledger: `$PFY_STATE_DIR/hedge-ledger.json` (`entries[]`, `spent`). Live spend from real providers is **not** tracked yet — T-0122. `DEPLOY_PROFILE=local-only` forbids the cloud lane regardless of budget.

| Task | local ready | budget left | lane |
|------|-------------|-------------|------|
| bulk / interactive | yes | any | local |
| bulk / interactive | no | yes | cloud |
| hard | any | yes | cloud (local named as hedge) |
| hard | yes | no | local |
| any | no | no | FAIL → `./pfy up` or set `PFY_CLOUD_BUDGET` |

### Failure modes

| Symptom | Likely cause | Recovery |
|---------|--------------|----------|
| `STUB toolset X → Y` | cell is `stub` (no config surface wired) | read `how`; implement the adapter; flip the cell honestly |
| `STUB plan -- … pfylib plan not ported (T-0121)` | cell is implemented/partial by its legacy script, plan body not yet in `pfylib` | run the listed `./pfy` command; port under T-0121 |
| `FAIL TypeSafe key missing (cloud lane)` | `jev --lane cloud` without `TYPESAFE_API_KEY` | set key or `--lane local` |
| `refused: outside …` | plan path not under state dir / harness home | set `GROK_HOME` / `CODEX_HOME` / `CLAUDE_CONFIG_DIR` or `PFY_STATE_DIR` |
| `FAIL hedge -- … cloud unavailable` | no local runtime and budget exhausted / `local-only` | `./pfy up` or `PFY_CLOUD_BUDGET=<n>` |

## Configuration / variables

| Var | Read by | Meaning |
|-----|---------|---------|
| `PFY_ROOT` | `registry.root()` | repo root override (default: two levels above `pfylib/`) |
| `PFY_STATE_DIR` | `registry.state_dir()` | state + ledger + briefs (default `~/.pfy-mentat`) |
| `PFY_CLOUD_BUDGET` / `PFY_CLOUD_TASK_COST` | `hedge` | credits for the period / credits per cloud decision |
| `DEPLOY_PROFILE` | `hedge` | `local-only` forbids cloud |
| `GROK_HOME`, `CODEX_HOME`, `CLAUDE_CONFIG_DIR` | `toolsets.harness_home()` | writable harness homes for `apply --yes` |
| `PFY_JEV_CONF_GATE`, `TYPESAFE_API_KEY`, … | via `scripts/pfy_jev_230.py` | Jev toolset knobs (see [jev-230.md](jev-230.md)) |

## Agent section

### Structural map

```
data/toolsets.json ─┐                         data/harnesses.json (role=harness)
                    ▼                                     ▼
            pfylib/registry.py  load / ids / validate() ──┘
                    │
            pfylib/toolsets.py  matrix() · plan(tid,hid,lane) · apply(plan, yes)
                    │                 └─ _plan_jev → pfylib/_legacy.py → scripts/pfy_jev_230.py (import, no copy)
            pfylib/hedge.py     decide(task, local, budget) · record() · ledger · detect_local() → scripts/detect-local-runtime.sh
                    │
            pfylib/cli.py       argparse: toolset list|matrix|plan|apply|validate · hedge decide|ledger|record
                    ▲
            scripts/pfy         `toolset` / `hedge` verbs: exec python3 "$ROOT/pfylib/cli.py" …
            scripts/catalog_check.py  → registry.validate() + tools.json `implementation` cross-check
            tests/              unittest, offline, tmp state dir
```

### Invariants

- The matrix status is derived from `data/toolsets.json` only; `plan()` never upgrades a `stub` and never fabricates a READY plan for an unported toolset.
- `plan()` is pure (no writes). `apply()` writes only with `yes=True` and only under allowed roots; every write mode is idempotent.
- Jev semantics live in `scripts/pfy_jev_230.py`; `pfylib` imports it by path via `_legacy` — do not copy constants or decision logic into `pfylib`. When T-0121 moves the module, `_legacy.jev()` becomes a normal import.
- `hedge.decide()` is deterministic given `(task, local, budget, ledger, profile)`; tests pass `local=` and `budget=` explicitly so no detector or network runs.
- `catalog_tool` is a `TOOLS.md`/`tools.json` **name** or `null`; the reverse link is `tools.json[].implementation = {"toolset", "stage"}` with stages from [integration-stages.md](../ops/integration-stages.md). Do not invent catalog rows or scores to make the link exist.
- Package is `pfylib/` because the repo root already has the executable file `pfy` (ADR-0017 § Consequences).

### Extension points (T-0121)

Add a `_plan_<toolset>()` in `toolsets.py`, dispatch on `tid` in `plan()`, import the legacy module through `_legacy.load("<script stem>")`, and flip the relevant cells in `data/toolsets.json` only to the status the code earns. Add a test in `tests/test_toolsets.py` asserting non-empty `env`/`brief` for every `implemented` cell.
