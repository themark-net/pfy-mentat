# Handoff — orch-fixes-1011-recheck — 2026-10-17

Verify-and-repair of the eight orch-fixes-1011 items on current main. One real gap. No pull request.

## Where

- Branch: `build/orch-fixes-1011-recheck`
- Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011-recheck`
- Base: `origin/main` `0d574f0649ccfe5bdd5d5384786c74173fb6e41e` (fetch showed no newer main commits)
- Drop-in: `b0e0b98` `docs: orch-fixes-1011 drop-in, re-checked against main 0d574f0`
- Item 2: `d78aa1599dcf18af782d80aa44feca371f5ed007` `smoke: item 2 timeout reasons use timeout_reason`
- Final head: `2ccee09998b0aa9964b880fc304d12b712007be2` (this handoff, the run log, and the decisions file). A later commit only inserts this SHA. `git rev-parse HEAD` on the branch is that later commit.
- Compare: https://github.com/themark-net/pfy-mentat/compare/main...build/orch-fixes-1011-recheck

## Exit

DONE (goal met). Stop file was absent. No item was SKIPPED. Baseline was green. Wall clock stayed inside the 6 hour cap (started 2026-10-17T12:05:55-07:00).

## Counts

| Suite | Result |
|-------|--------|
| Baseline, before any product edit | Ran 350 tests in 45.184s OK (skipped=4). `/tmp/pfylib-*` 8926 before and after. |
| Local CI full suite, after item 2 | Ran 352 tests in 47.341s OK (skipped=4). The extra two tests are the new overtime and festival timeout checks. `/tmp/pfylib-*` still 8926. |

`test_hedge` `test_detector_runs_offline` did not fail. `FAIL: grok not on PATH` is stdout from a test that passes.

## Items

| # | Status | Evidence |
|---|--------|----------|
| 1 | ALREADY-DONE | `examples/x-intake-local/smoke.py:175` `pinned()` records `expected.<VAR>.source` as `pin` or `env` and prints a stderr WARN when `HARNESS_SHA256`, `GRAPHJIN_SHA256`, or `CM_SHA256` is set. Tests: `test_d_repoharness_sha_unset_records_pin_and_does_not_exec`, `test_d_repoharness_sha_env_warns_records_override_and_does_not_exec`, `test_graphjin_sha_unset_records_pin_and_does_not_exec`, `test_graphjin_sha_env_warns_records_override_and_does_not_exec`, `test_cassmemory_sha_unset_records_pin_and_does_not_exec`, `test_cassmemory_sha_env_warns_records_override_and_does_not_exec`. |
| 2 | DONE | `d78aa15`. `smoke_112_114.py` and `smoke_115_116.py` wrote `timeout after <s>s: <cmd>` and now call `timeout_reason`. Receipt text is `overtime timeout`, `festival timeout`, or `openqodex timeout`. Red: 3 tests FAILED on the old sentence. Green: 12 tests OK in 9.810s, including `test_b_sponsio_timeout_reason_is_exact` (`sponsio probe timeout`). Mutation of each new assignment turned its test red; the lines were restored. Other smokes already used `timeout_reason`. |
| 3 | ALREADY-DONE | `docs/automation/agent-substrate-2026-10-08-handoff.md` spec-edit blocks. Both `python3` blocks ran in `/tmp` against a seed `b/config.json`. First set `root.path=/` and `readonly=true`. Second set `process.terminal=false` and left root alone. |
| 4 | ALREADY-DONE | `git add -f pipelines/smoke/<entry>/latest.json` is in the x-intake handoffs dated 2026-10-05, 06, 07, 09, 10, and 11. `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md` notes the temporary atg pin worktree was removed. |
| 5 | ALREADY-DONE | `git check-ignore -v` matches `.gitignore` lines 81-86 for rulora, har, cassmemory, bugpatrol, graphjin, and antislop. `pipelines/smoke/kolibri1/latest.json` is tracked and not ignored. `git status --porcelain pipelines/smoke` was empty. |
| 6 | ALREADY-DONE | `examples/x-intake-local/smoke_103_105.py` `graphjin_world` closes `serve.log` when `Popen` raises (`log.close()` in the `except` before `raise`). Test: `test_graphjin_world_closes_log_when_popen_raises`. |
| 7 | ALREADY-DONE | `smoke_106_108.py` `clean_env` points `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, and `npm_config_cache` under the temp HOME. A work dir outside that HOME FAILs. `.har/otel-hooks` is a hook file. Tests: `test_har_work_dir_outside_temp_home_fails`, `test_har_work_dir_sibling_prefix_fails`, `test_har_env_dirs_are_under_temp_home`, `test_har_otel_hooks_in_temp_home_fails`. |
| 8 | ALREADY-DONE | Baseline and the later full suite left `/tmp/pfylib-*` at 8926. `tests/test_pfylib_tmp_cleanup.py` `test_module_run_leaves_no_new_pfylib_tmp_dirs`. |

## Local CI

Every shell `run:` step in `.github/workflows/eval-structural.yml` (GitHub job and the self-hosted job; checkout and artifact upload skipped) exited 0. Structural PASS. Golden PASS. Gab, Jev, and launch-wizard selftests PASS. `catalog_check.py` PASS (`n_json=7`, `tools_md=51`, `stage_cards=51`). `check_no_encoded_payloads.py` PASS (67 files). `catalog_dashboard.py` and `smoke_contract_lint.py` PASS (8 example dirs). Jev `cua-s1-forms` smoke exit 0. `./pfy toolset matrix`, `./pfy toolset plan jev --harness opencode`, and `./pfy hedge decide --task bulk --local ready --budget 0` exit 0.

`pipelines/eval/golden.latest.md` only changed its timestamp. `pipelines/catalog/dashboard.latest.md` regenerated from the slim catalog. Both were restored and are not in this branch's diff.

## Decisions

Seven lines in `docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-orch-fixes-1011-recheck.md`.

## Not in this run

The follow-up list (`docs/build-dropins/pr284-followups.md`, including "no WARN when the override equals the pin") was not started. Later x-intake handoffs (2026-10-12, 14, 15, 16) were left as they are. No PR was opened. Nothing was pushed except `build/orch-fixes-1011-recheck`.
