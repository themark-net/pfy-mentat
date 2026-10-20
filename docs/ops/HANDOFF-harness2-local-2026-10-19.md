# Handoff — harness2-local (2026-10-19 name, run 2026-10-20)

Branch: `bot/h1-harness2`
Base: `aed526d080114f83fbd9ad329b4c9e5b62baf64c` (`origin/main`, equal)
Head: `da6d56a9ea711b3825ba406ca5f49cabe326b55d` on `bot/h1-harness2` (item 2 was `96408480a0fcfa29e6bff0963aa6f7ff58c313e6`; item 1 was `7243b2aef6a40603c8c10a4ca7b9e1ba3d4fe547`)
Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/h1-harness2
Proposal branch: none yet
Exit: none yet (run in progress)

## Status

| Item | Status |
|------|--------|
| 0 drop-in | ALREADY-DONE |
| 1 stage | DONE. Real stage re-run exit 0 (`stage: ok`, `check: ok`). HOME diff empty. Pins match. |
| 2 sandbox | DONE. 26 behavior tests OK in 46.054s. Real OpenCode run uses the config model. N1, N2, N5 PASS. |
| 2b fixes | 2b.1 DONE. 2b.2 DONE (28 sandbox tests OK in 51.530s). 2b.3, 2b.4, 2b.5 ALREADY-DONE in item 2. 2b.6 pending. |
| 3 adapter | pending |
| 4 surface | pending |
| 5 propose | pending |
| 6 live | pending |
| 7 docs | pending |
| N nimo checks | N1 PASS, N2 PASS, N5 PASS. N3, N4 held-out/pins, N6 not started. |

## Tests

- Baseline: `python3 -m unittest discover -s tests -t .` → 459 tests, OK (skipped=4), exit 0. The two previously known failures passed here and are not allow-listed.
- Item 1: `python3 -m unittest tests.test_harness2_local_stage` → Ran 8 tests in 132.068s, OK. Real `stage.sh` re-run exit 0.
- Item 2: `python3 -m unittest tests.test_harness2_local_sandbox` → Ran 26 tests in 46.054s, OK.
- Item 2b.1: same module → Ran 27 tests in 45.204s, OK.
- Item 2b.2: same module → Ran 28 tests in 51.530s, OK.

## RED

- unset `npm_config_cache` → `test_stub_tools_see_state_caches_and_home_stays`
- `--version` must be `1.14.18` → `test_stub_stage_exits_0_without_preflight_module_or_harness2_check` (`check: opencode --version printed 'local'`)
- vertex guard removed → `test_vertex_model_exits_2`
- Item 2 mutants are listed in the run log. All were restored. The cap-stub order reversal passed by accident (the sweep does not delete that regular file).
- 2b.1 `find -L` → `test_sweep_skips_symlinks_and_leaves_the_target` (socket deleted). Dropping the lstat skip → same test (symlink path passed to chmod and find). `chmod -R -L` stayed green on uutils 0.10.0 (PASS-BY-ACCIDENT, D8). Restored.
- 2b.2 no flock in `_acquire_call_lock` → `test_second_call_is_blocked_until_the_first_finishes` (B exited 0). Restored.

## Not verified yet

Local CI. Live receipt. Item 2b.6, then items 3 through 7. N3, N4 held-out/pins, N6.

Decisions: `docs/ops/AUTONOMOUS-DECISIONS-2026-10-19-harness2-local.md`
Run log: `docs/ops/RUN-LOG-harness2-local.md`
