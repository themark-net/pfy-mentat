# Handoff — harness2-local (2026-10-19 name, run 2026-10-20)

Branch: `bot/h1-harness2`
Base: `aed526d080114f83fbd9ad329b4c9e5b62baf64c` (`origin/main`, equal)
Head: item 1 commit on `bot/h1-harness2` (base `aed526d`)
Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/h1-harness2
Proposal branch: none yet
Exit: none yet (run in progress)

## Status

| Item | Status |
|------|--------|
| 0 drop-in | ALREADY-DONE |
| 1 stage | DONE. Real stage re-run exit 0 (`stage: ok`, `check: ok`). HOME diff empty. Pins match. |
| 2 sandbox | pending |
| 2b fixes | pending |
| 3 adapter | pending |
| 4 surface | pending |
| 5 propose | pending |
| 6 live | pending |
| 7 docs | pending |
| N nimo checks | pending |

## Tests

- Baseline: `python3 -m unittest discover -s tests -t .` → 459 tests, OK (skipped=4), exit 0. The two previously known failures passed here and are not allow-listed.
- Item 1: `python3 -m unittest tests.test_harness2_local_stage` → Ran 8 tests in 132.068s, OK. Real `stage.sh` re-run exit 0.

## RED

- unset `npm_config_cache` → `test_stub_tools_see_state_caches_and_home_stays`
- `--version` must be `1.14.18` → `test_stub_stage_exits_0_without_preflight_module_or_harness2_check` (`check: opencode --version printed 'local'`)
- vertex guard removed → `test_vertex_model_exits_2`

## Not verified yet

Local CI. Live receipt. Item 2 onward.

Decisions: `docs/ops/AUTONOMOUS-DECISIONS-2026-10-19-harness2-local.md`
Run log: `docs/ops/RUN-LOG-harness2-local.md`
