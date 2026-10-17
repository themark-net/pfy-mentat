# RUN LOG — orch-fixes-1011-recheck

Started: 2026-10-17T12:05:55-07:00
Worktree: /home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011-recheck
Branch: build/orch-fixes-1011-recheck
Base: origin/main 0d574f0649ccfe5bdd5d5384786c74173fb6e41e (fetch: HEAD is that commit plus the drop-in b0e0b98; origin/main has no newer commits)
Stop file: absent at start

Overview: Verify-and-repair of the eight orch-fixes-1011 items that landed on main as #289. Confirm each DoD on this tree. Repair only a real regression. The only gap found in the pre-pass is item 2: smoke_112_114.py and smoke_115_116.py write a timeout receipt reason without timeout_reason. Items 1, 3, 4, 5, 6, 7, and 8 look present and will be confirmed with commands. The pr284-followups list is out of scope.

Phases:
- baseline | tests/ | `python3 -m unittest discover -s tests -t .` recorded, including /tmp/pfylib-* before and after. Stop if red beyond test_hedge.TestHedge.test_detector_runs_offline. | none | general
- item-1-sha | examples/x-intake-local/smoke.py, smoke_098_100.py, smoke_103_105.py, smoke_106_108.py, tests/test_x_intake_smoke_098_100.py, tests/test_x_intake_smoke_103_105.py, tests/test_x_intake_smoke_106_108.py | Receipt expected sha has source pin or env for HARNESS_SHA256, GRAPHJIN_SHA256, CM_SHA256. Env override prints WARN. Tests cover pin and env. | baseline | general
- item-2-timeout | examples/x-intake-local/smoke.py, smoke_112_114.py, smoke_115_116.py, tests/test_x_intake_smoke_112_114.py, tests/test_x_intake_smoke_115_116.py, plus the sponsio test in tests/test_x_intake_smoke_098_100.py | Every smoke's timeout receipt reason comes from timeout_reason. A sponsio test asserts that text. Later smokes that bypass it are fixed. | baseline | general
- item-3-stage-a | docs/automation/agent-substrate-2026-10-08-handoff.md | Two spec-edit python blocks run against a temp config.json and change root.path, root.readonly, and process.terminal. | baseline | general
- item-4-handoff-docs | docs/automation/x-intake-2026-10-0{5,6,7,9}-handoff.md, x-intake-2026-10-{10,11}-handoff.md, docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md | git add -f sentence present on those handoffs. 2026-10-09 orch handoff notes the temp atg pin worktree was removed. | baseline | general
- item-5-gitignore | .gitignore, pipelines/smoke/ | git check-ignore passes for rulora, har, cassmemory, bugpatrol, graphjin, antislop receipt paths. kolibri1/latest.json stays tracked. | baseline | general
- item-6-graphjin-log | examples/x-intake-local/smoke_103_105.py, tests/test_x_intake_smoke_103_105.py | graphjin_world closes serve.log if Popen raises. Test asserts the handle is closed. | baseline | general
- item-7-har-home | examples/x-intake-local/smoke_106_108.py, tests/test_x_intake_smoke_106_108.py | FAIL when work_dir_under_temp_home is false. XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_DATA_HOME, npm_config_cache point under the temp HOME. ~/.har/otel-hooks inside that HOME fails the smoke. | baseline | general
- item-8-pfylib-tmp | tests/test_pfylib_tmp_cleanup.py and the mkdtemp modules it runs | A full suite leaves no new /tmp/pfylib-* directory. | baseline | general
- handoff | docs/ops/HANDOFF-orch-fixes-1011-recheck-2026-10-17.md, this log | Local CI recorded. Branch pushed. No PR. | all items | general

Risks:
- Baseline red for a reason other than the known box-only hedge detector test. Mitigation: record it and stop (BLOCKED: red-base). Do not patch around it.
- Item 2's new timeout text breaks an existing assertion that wants "timeout after". Mitigation: read those assertions first. The current 112 and 115 timeout tests check a substring or the real-HOME sentence, not the old full sentence. New assertions require the shared format.
- A full suite plus local CI on a busy host. Mitigation: one suite at a time. No benches. No second worktree.
- Follow-up refinements (WARN when the override equals the pin, later handoff wording) get pulled into this run. Mitigation: the decisions file names what is out of scope.

Exits checked at start: stop-file absent. Clock started 2026-10-17T12:05:55-07:00. New items allowed until 2026-10-17T17:35:55-07:00. Hard stop about 2026-10-17T18:05:55-07:00.

## Results

- baseline | DONE | tests: `python3 -m unittest discover -s tests -t .` → Ran 350 tests in 45.184s OK (skipped=4), exit 0. `test_detector_runs_offline` did not fail. The line `FAIL: grok not on PATH` is a passing test's stdout. `/tmp/pfylib-*` was 8926 before and 8926 after. `docs/NEXT.md` is absent. | files: 0 | err: none
- item-1-sha | ALREADY-DONE | tests: covered by the baseline suite. Evidence on origin/main: `examples/x-intake-local/smoke.py:175` `pinned()` writes `expected.<VAR>.source` as `pin` or `env` and prints `WARN: $<VAR>=... overrides the pinned ...` when the env value is set. Call sites: `smoke_098_100.py` `HARNESS_SHA256`, `smoke_103_105.py` `GRAPHJIN_SHA256`, `smoke_106_108.py` `CM_SHA256`. Tests: `test_d_repoharness_sha_unset_records_pin_and_does_not_exec`, `test_d_repoharness_sha_env_warns_records_override_and_does_not_exec`, `test_graphjin_sha_unset_records_pin_and_does_not_exec`, `test_graphjin_sha_env_warns_records_override_and_does_not_exec`, `test_cassmemory_sha_unset_records_pin_and_does_not_exec`, `test_cassmemory_sha_env_warns_records_override_and_does_not_exec`. | files: 0 | err: none
- item-2-timeout | DONE | tests: red before the fix, `Ran 3 tests` FAILED. Reasons were `timeout after 0.4s: [...]` and `timeout after 1.0s: [...]`, not `overtime timeout` / `festival timeout` / `openqodex timeout`. Green after: `python3 -m unittest tests.test_x_intake_smoke_112_114 tests.test_x_intake_smoke_115_116 tests.test_x_intake_smoke_098_100.XIntakeSmoke098100Tests.test_b_sponsio_timeout_reason_is_exact` → Ran 12 tests in 9.810s OK. Mutation: replacing each `timeout_reason(...)` assignment with a `timeout after` string made that test fail (`timeout after 0.4s`, `timeout after festival`, `timeout after openqodex`); lines restored. Sponsio test `test_b_sponsio_timeout_reason_is_exact` still expects `sponsio probe timeout`. Other smokes already call `timeout_reason` (098-111, 117-124). `steps[].daemon_stop = "timeout"` left as a step status. | files: 4 | err: none | commit d78aa1599dcf18af782d80aa44feca371f5ed007
- item-3-stage-a | ALREADY-DONE | tests: ran the two python blocks from `docs/automation/agent-substrate-2026-10-08-handoff.md` (root path read-only at the first block, `process.terminal` false at the second) in `/tmp/stage-a-spec-*` against a seed `b/config.json`. block1 set `root.path=/` and `readonly=true`. block2 set `process.terminal=false` and left root alone. The `runsc` / `unshare` block was not run. | files: 0 | err: none
- item-4-handoff-docs | ALREADY-DONE | tests: doc read. `git add -f pipelines/smoke/<entry>/latest.json` is in `docs/automation/x-intake-2026-10-05-handoff.md`, `x-intake-2026-10-06-handoff.md`, `x-intake-2026-10-07-handoff.md`, `x-intake-2026-10-09-handoff.md`, `x-intake-2026-10-10-handoff.md`, and `x-intake-2026-10-11-handoff.md`. `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md` says the temporary atg pin worktree was removed. Later handoffs (2026-10-12, 14, 15, 16) were not edited. | files: 0 | err: none
- item-5-gitignore | ALREADY-DONE | tests: `git check-ignore -v` matches `.gitignore` lines 81-86 for `pipelines/smoke/{rulora,har,cassmemory,bugpatrol,graphjin,antislop}/latest.json`. `git ls-files --error-unmatch pipelines/smoke/kolibri1/latest.json` succeeds. `git check-ignore` does not match kolibri1. `git status --porcelain pipelines/smoke` empty. | files: 0 | err: none
- item-6-graphjin-log | ALREADY-DONE | tests: covered by the baseline suite. `examples/x-intake-local/smoke_103_105.py` `graphjin_world` closes `serve.log` in `except Exception` before re-raising when `Popen` fails (the `log = open` / `except` / `log.close()` block). Test: `test_graphjin_world_closes_log_when_popen_raises`. | files: 0 | err: none
- item-7-har-home | ALREADY-DONE | tests: covered by the baseline suite. `smoke_106_108.py` `clean_env` sets `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME`, and `npm_config_cache` under the temp HOME. A work dir that fails `Path.is_relative_to` sets `work_dir_under_temp_home` false and reason `work dir is not under the temp HOME`. `HOOK_FILES` includes `.har/otel-hooks`. Tests: `test_har_work_dir_outside_temp_home_fails`, `test_har_work_dir_sibling_prefix_fails`, `test_har_env_dirs_are_under_temp_home`, `test_har_otel_hooks_in_temp_home_fails`. | files: 0 | err: none
- item-8-pfylib-tmp | ALREADY-DONE | tests: baseline full suite left `/tmp/pfylib-*` at 8926. `tests/test_pfylib_tmp_cleanup.py` `test_module_run_leaves_no_new_pfylib_tmp_dirs` ran inside that suite. `addCleanup(shutil.rmtree, ...)` is on the cli, toolset, hedge, loop, and attach mkdtemp dirs. | files: 0 | err: none

Local CI (every `run:` shell step in `.github/workflows/eval-structural.yml`, both jobs, skipping checkout and artifact upload): all exit 0.
- structural PASS (includes `Ran 352 tests in 47.717s · OK (skipped=4)` inside the harness)
- golden PASS
- `PFY_GAB_OFFLINE=1 python3 scripts/pfy_gab_228.py --selftest` PASS
- `PFY_JEV_OFFLINE=1 python3 scripts/pfy_jev_230.py --selftest` PASS
- `python3 scripts/pfy_launch_wizard_225.py --selftest` PASS
- `PFY_STATE_DIR=/tmp/pfy-orch-recheck-state python3 -m unittest discover -s tests -t .` → Ran 352 tests in 47.341s OK (skipped=4). The two tests added for item 2 are the difference from the 350 baseline.
- `python3 scripts/catalog_check.py` PASS n_json=7 toolsets=8 linked=2 catalog_tool=null:6 tools_md=51 stage_cards=51 i1_cards_open=0 stage_only=4
- `./pfy toolset matrix`, `./pfy toolset plan jev --harness opencode`, `./pfy hedge decide --task bulk --local ready --budget 0` exit 0
- launcher filemode, `bash -n`, `py_compile`, `./pfy help` exit 0
- `python3 scripts/check_no_encoded_payloads.py --selftest` and the check itself PASS (67 tracked files)
- `python3 scripts/catalog_dashboard.py` exit 0
- `python3 scripts/smoke_contract_lint.py` PASS smoke contract 8 example dirs
- `PFY_JEV_OFFLINE=1 python3 scripts/pfy_jev_230.py --smoke cua-s1-forms` exit 0
- `pipelines/eval/golden.latest.md` and `pipelines/catalog/dashboard.latest.md` were regenerated and restored with `git checkout --`. `/tmp/pfylib-*` still 8926 after the second full suite.

Exits checked before item 2 and before this close-out: stop-file absent. Skips in a row: 0. No identical-failure loop. Baseline was green. Clock from 2026-10-17T12:05:55-07:00, still inside the window. Exit: DONE (goal met).
