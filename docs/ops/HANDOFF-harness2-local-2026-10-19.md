# Handoff: harness2-local (2026-10-19 name, run 2026-10-20)

Branch: `bot/h1-harness2`
Base: `aed526d080114f83fbd9ad329b4c9e5b62baf64c` (launch `origin/main`). Later `origin/main` moved for Hermes eval. This branch is not merged with that tip.
Head: `4bd065de7a2366149dac47f4c9cf964e31e65f20` on `bot/h1-harness2` (item 5). Docs tip after this recording commit is one commit ahead. Item 2c was `a785c27e88945791de0e9a658dd6f2bdfa53f308`; item 4 was `475f34ddc8736969db253e3ed654fd85f8bbaea1`; the stop-file docs commit was `e240d5b47024f5102ba0c6939f3fc9e9472434ce`; item 3 was `3260e0228cee5344578bfad2a26076ef43bb03ec`; resume base `902e04f47eaf7c7083b80062235a056c63352f63`.
Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/h1-harness2
Proposal branch: none
Exit: STOPPED_EXIT: stop-file (`$W/tmp/STOP`, empty, mtime 2026-10-20 12:13 PDT)

## Status

| Item | Status |
|------|--------|
| 0 drop-in | ALREADY-DONE |
| 1 stage | DONE. Real stage re-run exit 0 (`stage: ok`, `check: ok`). HOME diff empty. Pins match. |
| 2 sandbox | DONE. 26 behavior tests OK in 46.054s at item 2. The module is 40 tests after item 2c. N1, N2, N5 PASS. |
| 2b fixes | DONE. 2b.1 and 2b.2 committed. 2b.3, 2b.4, 2b.5 ALREADY-DONE in item 2. 2b.6 cites managed.ts:30 and config.ts:619-623. |
| 2c fixes | DONE. Tester FAIL of `902e04f`: idle 600 s, caller XDG wins, sbun exposes the relay port, watchdog gap 10 s after a miss, mutant tests, hermetic stage, executor XDG, checkout refusal, em dashes in headings. Full suite 520 OK (skipped=4) in 424.657s. |
| 3 adapter | DONE. Commit `3260e0228cee5344578bfad2a26076ef43bb03ec`. 8 tests OK in 62.360s. |
| 4 surface | DONE. Commit `475f34ddc8736969db253e3ed654fd85f8bbaea1`. 5 tests OK in 0.426s. |
| 5 propose | DONE. Commit `4bd065de7a2366149dac47f4c9cf964e31e65f20`. 20 tests OK. Full suite 540 OK (skipped=4) in 427.292s. |
| 6 live | not started |
| 7 docs | not started (stop-file) |
| N nimo checks | N1 PASS, N2 PASS, N5 PASS. N3, N4 held-out/pins, N6 not started. |

## Tests

- Baseline: `python3 -m unittest discover -s tests -t .` → 459 tests, OK (skipped=4), exit 0. The two previously known failures passed here and are not allow-listed.
- Item 1: `python3 -m unittest tests.test_harness2_local_stage` → Ran 8 tests in 132.068s, OK. Real `stage.sh` re-run exit 0.
- Item 2: `python3 -m unittest tests.test_harness2_local_sandbox` → Ran 26 tests in 46.054s, OK.
- Item 2b.1: same module → Ran 27 tests in 45.204s, OK.
- Item 2b.2: same module → Ran 28 tests in 51.530s, OK.
- Item 3: `python3 -m unittest tests.test_harness2_local_cases tests.test_harness2_local_drive` → Ran 8 tests in 62.360s, OK. Re-run after item 4's `write_base`: Ran 8 tests in 62.413s, OK.
- Item 4: `python3 -m unittest tests.test_harness2_local_surface` → Ran 5 tests in 0.426s, OK.
- Baseline remains 459 OK (skipped=4) at `aed526d`. H1b resume suite was 498 OK (skipped=4). H1c resume suite, before item 2c edits, was 508 OK (skipped=4) in 377.550s. After item 2c: Ran 520 tests in 424.657s, OK (skipped=4).
- Item 5: `python3 -m unittest tests.test_harness2_local_propose` → Ran 20 tests in 1.962s, OK. Full suite after that: Ran 540 tests in 427.292s, OK (skipped=4).

## RED

- unset `npm_config_cache` → `test_stub_tools_see_state_caches_and_home_stays`
- `--version` must be `1.14.18` → `test_stub_stage_exits_0_without_preflight_module_or_harness2_check` (`check: opencode --version printed 'local'`)
- vertex guard removed → `test_vertex_model_exits_2`
- Item 2 mutants are listed in the run log. All were restored. The cap-stub order reversal passed by accident (the sweep does not delete that regular file).
- 2b.1 `find -L` → `test_sweep_skips_symlinks_and_leaves_the_target` (socket deleted). Dropping the lstat skip → same test (symlink path passed to chmod and find). `chmod -R -L` stayed green because the fixture modes were 600 and 700, which `u+rwX` cannot change. The cause was the fixture, not uutils (D8, corrected by D13). With modes 400 and 500 the same mutant changes the target and the test goes red. Restored.
- 2b.2 no flock in `_acquire_call_lock` → `test_second_call_is_blocked_until_the_first_finishes` (B exited 0). Restored.
- Item 3 mutants are listed in the run log. All were restored. The visible key-order failures after the assert reorder are `first=24 last=9`, `first=9 last=24`, and `'local' unexpectedly found in 'wz-01-local-30b'`. Sorted-only fails the order-preserving pin (`eb00a397` != `ab0ee29b`).
- Item 4: `rule_edits` returns `[]` → `test_guardrail_edit_is_rejected` (`0 != 2`). `enforce_path_allow` returns `[]` → `test_disallowed_paths_are_named` (`0 != 2`). Restored.
- Item 2c RED lines are in the run log. All mutants were restored. The 0.2 s watchdog gap kills the 12 s blackout (`relay down`). A 6 s stall of one request stayed green under that mutant (22.8 s) and is not the proof.
- Item 5 RED lines are in the run log. All mutants were restored. `GAIN_MIN = 1` pushes a +1 gain. Removing the secret scan pushes the fake tokens. `sk-|xai-` rejects `task-specific`. `ghp_` alone lets `gho_` through. Removing the leak check pushes `label: B correct`. Bare labels, and case-insensitive letters, block more than `case 3 - A`. Dropping the protected-name check pushes `main-2`.

## Not verified yet

Local CI was not run. No live receipt. No llama-server was started. Items 6 and 7. N3, N4 held-out/pins, N6.

The Exit line above is the H1b stop-file. This session has not exited.

Next step: item 6, the live run, if it can start by 2026-10-20T16:38:06-07:00. Else BLOCKED: no-time-for-live, with the other items pushed. Stop by 2026-10-20T19:53:06-07:00.

Decisions: `docs/ops/AUTONOMOUS-DECISIONS-2026-10-19-harness2-local.md`
Run log: `docs/ops/RUN-LOG-harness2-local.md`
