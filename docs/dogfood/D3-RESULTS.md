# Dogfood D3 results — measure + trim `./pfy build -p` preamble (#263)

**Base:** `cbda54a` (#262)  
**Branch / worktree:** `bot/dogfood-d3-263` · `/home/mark/DEVELOP/pfy-mentat/tmp/dogfood-d3-263`  
**Lane:** bot only. Cite #263 only.

## Question

Is the toolset/skills preamble a large share of D2’s ~623k tokens, and can `./pfy build -p` measure + trim it while keeping the jev gate and exit-3 escalate contract?

## What landed (Build run 1)

`scripts/pfy_build_p.py`:

- Default **trimmed** preamble: jev conf gate ~0.85, route exits **0** ready / **3** escalate / **1** broken, receipt hint, skill **pointer** (not full body).
- `PFY_BUILD_FULL_PREAMBLE=1`: inlines jev brief + full skill bodies; keeps real `GROK_HOME`.
- Trimmed mode isolates child `GROK_HOME` to `pipelines/dogfood/build/<ts>/grok-home` with pointer skill + copied `auth.json` only (user skills tree not copied).
- Receipt `start` / `grok_p`: `preamble_chars`, `preamble_tokens_est` (method **`chars/4`**), `task_prompt_*`, `preamble_mode`.

Tests in `tests/test_pfy_build_p.py` (`PreambleTrimTests`): bound trimmed ≤ 400 tokens_est and ≤ 0.25× full; gate + exit-3 present; receipt field present; child home isolation. **FAIL on cbda54a, PASS on head** (proven).

## Build runs

| Run | Purpose | Receipt | rc | Wall (grok_p) | Turns | Model calls | Total tokens | Route |
|-----|---------|---------|----|---------------|-------|-------------|--------------|-------|
| 1 | Implement (preamble still **untrimmed** / real GROK_HOME — code not landed yet) | `pipelines/dogfood/build/20261005T072104Z/` | 0 | 626.227 s | 1 | 28 | **2 304 367** (in 2 252 271 · out 52 096 · cached read 2 108 672) | escalate / exit **3** |
| live measure (outer) | Tiny task with **trimmed** preamble | `pipelines/dogfood/build/20261005T073546Z/` | 0 | 5.923 s | 1 | 1 | **14 959** (in 14 596 · out 363 · cached read 10 240) | escalate / exit **3** |

Session ids: implement `01a10af0-082f-7900-a931-b0f83af4c593`; trimmed measure `01a10afd-7d8d-7012-a812-7bac558eeb7f`. TypeSafe tokens **0**. Trimmed stdout: `D3_TRIM_OK`.

## Preamble size (chars/4)

| Mode | Chars | `preamble_tokens_est` |
|------|------:|----------------------:|
| trimmed | 346 | **87** |
| full (`PFY_BUILD_FULL_PREAMBLE=1`) | 4654 | **1164** |
| ratio trimmed/full | | **~0.075** (bounds ≤ 0.25 and ≤ 400) |

Task prompt (measure): 33 `task_prompt_tokens_est`, recorded separately.

## Live token comparison vs D2 (~623k)

| | D2 (#262) | D3 trimmed measure |
|--|----------:|-------------------:|
| Total tokens | 623 246 | **14 959** (~2.4% of D2) |
| Input / output | 607 566 / 15 680 | 14 596 / 363 |
| Cached read | 503 936 | 10 240 |
| Model calls | 13 | 1 |
| Avg input / call | ~46 736 | ~14 596 |

**Which run used the trimmed preamble:** the **extra small live measure** after Build landed the code (not Build run 1). Build run 1 necessarily used the old full skill tree.

## Token-study findings

Method: preamble `chars/4`; live totals from `usage.json` / receipt.

1. **User skills dump is large.** `~/.grok/skills` text ≈ **150 265** bytes ≈ **37 567** tokens_est. D2’s 13 calls × a large per-call system/skills context (avg ~47k input, **~83% cached**) explains most of the 623k burn — not the tiny task prompt.
2. **Explicit trimmed preamble is tiny (87 tokens_est)** and is not the live 15k — Grok still pays a base context (tools/system). Isolating `GROK_HOME` dropped user skills; an empty home also caused Grok to **rehydrate `bundled/`** into the receipt dir (bundled text ≈ 823 KB on disk; not all inlined each call, but init cost/friction).
3. **Per-call preamble × model calls** is the amplifier: D2 13 calls with fat skills vs trimmed 1 call with pointer skills → ~42× total-token drop on a trivial task (not apples-to-apples task size, but same harness path).

### One concrete trim suggestion

Seed the isolated `GROK_HOME` by **symlinking** the real home’s `bundled/` (read-only) and writing only `auth.json` + pointer `skills/pfy-jev-decision/`, instead of starting from an empty home that triggers a full bundled rehydrate into `pipelines/dogfood/build/<ts>/grok-home/`. Keeps user skills out; avoids copying megabytes of bundled assets into every receipt (and never commit that tree — see `.gitignore`).

## Friction

1. Build run 1 burned **2.3M** tokens implementing the trim (fat skills still loaded) — expected chicken/egg.
2. Nohup outer log can stay empty; receipt + session usage are SoT.
3. Isolated `GROK_HOME` contains `auth.json` — **must not commit**; gitignored `pipelines/dogfood/build/**/grok-home/`.
4. Fail-on-base: new `PreambleTrimTests` → **FAILED (3 failures + 1 error)** against `cbda54a` `pfy_build_p.py`; **10 OK** on head.

## Outer-bot edits (not Build)

| File | Reason |
|------|--------|
| `docs/dogfood/D3-RESULTS.md` | Complete metrics, token study, live measure, outer-bot list (Build stub expanded) |
| `docs/PENDING-HANDOFF.md` | Refresh with live trimmed numbers + next steps |
| `.gitignore` | Ignore `pipelines/dogfood/build/**/grok-home/` (auth + rehydrate) |

Build-owned code/docs otherwise: `scripts/pfy_build_p.py`, `scripts/pfy`, `tests/test_pfy_build_p.py`, `docs/modules/jev-230.md`, `docs/ops/jev-230.md`, initial handoff/D3 stub.

## Catalog honesty

Toolset `jev` only. HOLD 70–75 untouched. No GUI / #258 / #256.
