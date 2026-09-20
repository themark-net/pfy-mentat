# OQ-0013: Code layout — `pfy/` Python package by concept + `tests/` + pytest in G0?

- **Priority:** **P1**
- **Status:** **open** (needs owner; 2026-09-20)
- **Blocks:** T-0111 (consolidation of `scripts/pfy_*_NNN.py`)
- **Related:** [critical-review-2026-09-20.md](../ops/critical-review-2026-09-20.md) §3.2–3.3 · OQ-0011 · OQ-0012 · ADR-0012 (launch)

## Question

**Question:** Should `scripts/pfy_*_NNN.py` move into a `pfy/` Python package named by concept with `tests/` + pytest in G0, and does bash `scripts/pfy` stay as a thin dispatcher or get ported?

`scripts/` holds **21 issue-numbered modules** (12,868 lines, 63 % of `scripts/`) that import each other by file path (`importlib.util.spec_from_file_location(...)`) and duplicate heavily (`pfy_attach_usable_196 ↔ 202` 91 % similar, `220 ↔ 221` 90 %; 14 functions defined identically in 4 of 5 attach files). There is no package, no importable namespace, and therefore no unit tests — only `--selftest` flags, 3 of 15 run in CI. `scripts/pfy` is a 1,924-line bash program.

**What is the target layout, and does bash `scripts/pfy` stay?**

## Proposed target (for the owner to accept, amend, or reject)

```text
pfy/                          # importable package (python3 -m pfy …)
  __init__.py
  cli.py                      # argparse dispatcher; verbs from a table
  runtime/                    # detect-local-runtime, endpoint, models (ex #161/#165/#207)
  attach/                     # ONE implementation + harness table (ex 162/193/196/202/220/221)
  board/                      # ex pfy-board.py (server + snapshot)
  gui/                        # ex pfy-gui.py (tk / webkit)
  catalog/                    # ex 209 / 214
  lanes/                      # ex 213 orchestration, 215 code-graph, 205 opencontext, 228 gab
  decision/                   # ex 230 jev
  wizard/                     # ex 224 / 225
tests/                        # pytest; offline fixtures moved out of --selftest
scripts/pfy                   # thin bash: env + exec python3 -m pfy "$@"   (or removed; see options)
```

Rules that go with it: modules named by **concept**, issue numbers only in docstrings/commit messages; one Attach implementation parameterised by `data/harnesses.json`; every module gets `tests/test_<module>.py`; G0 runs `pytest -q`.

## Options

### Option A — Package + thin bash dispatcher

- `scripts/pfy` keeps only: resolve `ROOT`, detect runtime, `exec python3 -m pfy "$@"`. Bash stays < 100 lines (filemode gate still applies).
- Consequence: `./pfy` keeps working on a box with only bash + python3; bash logic (1,924 lines) migrates in slices; lowest risk.

### Option B — Package, port bash fully to Python, `pfy` root wrapper only

- `scripts/pfy` removed; root `./pfy` = `exec python3 -m pfy`.
- Consequence: one language, one test suite; larger one-shot migration; `detect-local-runtime.sh` stays or becomes Python too.

### Option C — Keep flat `scripts/`, just rename files by concept and dedupe attach

- Minimum change: `pfy_attach_usable_*.py` → one `attach.py`; rename others; no package, no pytest.
- Consequence: cheap, but path-imports and `--selftest`-only testing remain; does not unlock unit tests.

### Option D — Do nothing until OQ-0011 decides what survives

- If OQ-0011 → A or C, most of these modules move to `examples/` and only `runtime/` + `attach/` need a package.
- Consequence: avoids refactoring code that will be parked; delays tests.

## Constraints regardless of option

- No encoded/sharded source (`scripts/check_no_encoded_payloads.py` gate, this PR).
- `./pfy help / status / harness list` output stays byte-identical across the move (baseline captures in the review §7).
- Existing `--selftest` behaviour kept until pytest coverage replaces it.

## What the owner needs to answer

1. A / B / C / D (recommendation: **A**, staged after OQ-0011; or D if OQ-0011 will land soon).
2. Whether the Tauri GUI (`gui/operator/`) stays in-repo or moves to its own repo once `pfy/gui/` exists.
3. Python floor (3.10? 3.12 as in CI?) so type hints / `match` can be used.

## Resolution notes

*(pending)*
