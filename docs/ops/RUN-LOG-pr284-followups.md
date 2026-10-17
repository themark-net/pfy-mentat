# RUN-LOG pr284-followups

Start: 2026-10-17T12:24:43-07:00
Worktree: /home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups
Branch: build/pr284-followups
Base: origin/main 0d574f0649ccfe5bdd5d5384786c74173fb6e41e (HEAD was 3b7439e, the drop-in)
Compare: https://github.com/themark-net/pfy-mentat/compare/main...build/pr284-followups
Remote note: origin/build/orch-fixes-1011-recheck is 0d574f0 plus docs and d78aa15 (timeout_reason in smoke_112_114.py and smoke_115_116.py, plus tests). Not merged. Do not undo those lines.

## Plan

Overview: Close the twelve X-intake smoke follow-ups that are still open on origin/main 0d574f0. Verify each item first. Change only the gap. One commit per item that changes files. Push only build/pr284-followups. No pull request.

Phases:
- item-1-sha-warn | examples/x-intake-local/smoke.py, tests/test_x_intake_smoke_098_100.py, tests/test_x_intake_smoke_103_105.py, tests/test_x_intake_smoke_106_108.py | HARNESS_SHA256, GRAPHJIN_SHA256, CM_SHA256 receipts keep expected value/source/pin; WARN only when the env override differs from the pin (sha compare is case-insensitive); equal override prints no WARN. Real stub smokes. Mutation: drop the equality check and the equal-pin test goes red. | none | general
- item-2-timeout-text | examples/x-intake-local/smoke_112_114.py, smoke_115_116.py, examples/x-intake-local/README.md, tests for 112 and 098 | Every recorded timeout reason is timeout_reason(tag), including 112-124. README says the same text. Sponsio test drives PFY_XINTAKE_TIMEOUT and goes red if the text changes. Keep d78aa15's approach. | none | general
- item-3-stage-a | docs/automation/agent-substrate-2026-10-08-handoff.md | Each Stage A spec-edit block runs against a temp spec under /tmp and the JSON matches. Commands do not depend on cwd. | none | general
- item-4-handoff-counts | docs/automation/x-intake-2026-10-11-handoff.md, maybe x-intake-2026-10-10-handoff.md | Rerun unittest at a5c0362 and fb3beb5 in throwaway /tmp worktrees and fix only a wrong "190 tests" sentence. | none | general
- item-5-gitignore | .gitignore, tests | 103-111 receipt dirs stay ignored, kolibri1/latest.json stays tracked, a test runs each 103-111 smoke into pipelines/smoke and git status --porcelain pipelines/smoke is empty. | none | general
- item-6-graphjin-log | examples/x-intake-local/smoke_103_105.py, tests/test_x_intake_smoke_103_105.py | serve.log closed on Popen raise, early server exit, and the normal path; tail read after flush; no ResourceWarning under -W error::ResourceWarning. | item-1 (same test file; land after) | general
- item-7-xdg | examples/x-intake-local/smoke_106_108.py, tests/test_x_intake_smoke_106_108.py | har FAILs when the work dir is outside the temp HOME; rulora, har, and cass-memory children get the four XDG/npm paths under that HOME. | item-1 | general
- item-8-tmp-cleanup | tests/test_pfylib_tmp_cleanup.py and any leaking test | Full-suite before/after diff of /tmp/pfylib-* and the smoke/launcher prefixes is empty. | later items, run the diff after they land | general
- item-9-paid-keys | examples/x-intake-local/smoke_098_100.py, tests/test_x_intake_smoke_098_100.py | Child env for sponsio, opensteps, and repoharness uses smoke.PAID_KEYS. Dummy values never arrive. | item-1 | general
- item-10-node-env | smoke_103_105.py, smoke_106_108.py, their tests | node --version uses the stripped child env (no PAID_KEYS, temp HOME). Mutation: pass os.environ and the test goes red. | item-7 | general
- item-11-109-tests | tests/test_x_intake_smoke_109_111.py, smoke_109_111.py only if the behavior is missing | Temp receipt dir via PFY_SMOKE_RECEIPT_DIR; no-bwrap fallback asserted; --unshare-pid asserted, including when unsupported. pipelines/smoke unchanged after the module. | none | general
- item-12-smolvm-digest | smoke_109_111.py, tests, sources/entries/109-smolvm.md, 2026-10-11 handoff | Receipt records image ref and resolved digest. Live nimo run only if the binary and /dev/kvm are already usable; otherwise BLOCKED for the live part. | item-11 if the same files change; sequence after it | general
- handoff | docs/ops/HANDOFF-pr284-followups-2026-10-17.md, this log | Final head, counts, per-item status, mutation notes, local CI, decisions, exit. | all items | general

Risks:
- Red base beyond test_hedge test_detector_runs_offline stops the run.
- A full suite inside another full suite would load the host. The cleanup test covers the leaking modules; one full-suite before/after diff is recorded in this log, not nested.
- origin/fix/x-intake-122-124-followups is not an ancestor. Main already has PFY_SMOKE_RECEIPT_DIR and the content-hash watch. Do not port that branch.
- Item 4 worktrees live only under /tmp and are removed. Never touch other worktrees under ~/DEVELOP/pfy-mentat/tmp.

## Baseline

`python3 -m unittest discover -s tests -t .` started on the unmodified tree (350 `def test_` methods at 3b7439e).
Result: Ran 350 tests in 45.371s OK (skipped=4) exit 0.
The known box-only `tests.test_hedge.DetectorTests.test_detector_runs_offline` did not fail on this host.
No red base.

## Items

- item-1-sha-warn | DONE | tests: before the fix, the three equal-pin tests FAILED (failures=6) because WARN printed when the env value equalled the pin. After the fix, the pin/mismatch/equal set Ran 9 tests OK. Mutation (WARN on every env value, equality check removed) made the three equal tests FAILED (failures=6); restored, Ran 3 tests OK. | files: smoke.py + 3 test modules | err: none | commit 8029a82
- item-2-timeout-text | DONE | tests: before the fix, overtime/festival/daemon-stop/openqodex FAILED (failures=4) on `timeout after <s>s: <cmd>` and bare `timeout`. After, those four plus sponsio Ran 5 tests OK. Mutation (`timeout_reason` returned `{tag} timed out`) made sponsio and overtime FAILED (failures=2); restored, Ran 5 tests OK. Grep of smoke*.py has no other recorded timeout sentence (one comment in smoke_122_124.py). README states `{tag} timeout`. Kept d78aa15's approach and also changed daemon_stop. | files: smoke_112_114.py, smoke_115_116.py, README, two test modules | err: none | commit 2d51881
- item-3-stage-a | DONE | tests: the old root-path edit, run from `/tmp`, exited 1 (NotADirectoryError on `b/config.json`). After the rewrite, all 4 extracted bash blocks ran with cwd `/tmp`, `STAGE_A` under `/tmp`, and a stub `runsc`. Final JSON root `{path: /, readonly: true}`, `process.terminal` false, args `["true"]`. The restore block's unshare reached the stub for run, checkpoint, delete, restore, kill, delete. Real runsc is not installed. | files: agent-substrate-2026-10-08-handoff.md | err: none | commit 9e4061f
- item-4-handoff-counts | DONE | tests: `git worktree add --detach /tmp/pfy-109-111 a5c0362` then unittest discover: Ran 191 tests in 5.479s OK (skipped=4) exit 0. Worktree removed. `git worktree add --detach /tmp/pfy-fb3beb5 fb3beb5`: Ran 190 tests in 3.953s OK (skipped=4) exit 0. Worktree removed. 2026-10-11 sentence now says 191. 2026-10-10 sentence kept (190 matches). | files: x-intake-2026-10-11-handoff.md | err: none | commit ca4dc7e
- item-5-gitignore | DONE | tests: the new skip-path test was green on the existing ignore lines (Ran 1 test OK). Mutation (comment out `pipelines/smoke/smolvm/`) made it FAIL with `?? pipelines/smoke/smolvm/`. Restored, Ran 1 test OK, and `git status --porcelain pipelines/smoke` is empty. kolibri1/latest.json stays tracked. No smoke wrote an extra dir. | files: tests/test_x_intake_smoke_103_111_receipts.py | err: none | commit 598c602
- item-6-graphjin-log | DONE | tests: Popen-raise and early-exit tests were already green on current graphjin_world (`python3 -W error::ResourceWarning` Ran 2 tests OK; the module Ran 5 tests OK). No smoke code change. Mutation: drop the except `log.close()` and the Popen test FAIL (`False is not true`) plus ResourceWarning. Drop the finally `log.close()` and the early-exit test FAIL the same way, with ResourceWarning on serve.log. Both closes restored. The early-exit receipt contains `pfy-serve-log-tail`, read after `log.flush()`. | files: tests/test_x_intake_smoke_103_105.py | err: none | commit 12733a3
- item-7-xdg | DONE | tests: new rulora and cass stubs dump env and cwd; both plus the existing har outside-work-dir test Ran 3 tests OK on current clean_env. Har already FAILs with "not under the temp HOME" (test_har_work_dir_outside_temp_home_fails, already on main). Mutation: drop the four dir assignments from clean_env and the rulora and cass tests ERROR KeyError XDG_CONFIG_HOME. Restored. | files: tests/test_x_intake_smoke_106_108.py | err: none | commit 11511a5
- item-8-tmp-cleanup | DONE | tests: extended tests/test_pfylib_tmp_cleanup.py Ran 1 test OK in 47.457s (launcher + x-intake modules, diff empty). Mutation: drop test_cli addCleanup rmtree and the same test FAIL with 13 new /tmp/pfylib-cli-* dirs. Restored and removed those 13 dirs. Full suite before/after diff of the same prefixes plus pfy-build- was empty (added 0, removed 0). Suite: Ran 360 tests in 97.942s OK (skipped=4). Pre-existing /tmp/pfylib-test-* (9060) were left in place. | files: tests/test_pfylib_tmp_cleanup.py | err: none | commit c6ec88a
- item-9-paid-keys | DONE | tests: before the scrub, test_e FAILED because the sponsio child received all 22 PAID_KEYS names (dummy value pfy-test-dummy, names only in the failure). After tool_env, the 098 module Ran 10 tests OK, including sponsio, opensteps, and repoharness children. Mutation: drop the PAID_KEYS filter and test_e FAILED the same way (22 names). Restored. Git still uses run() with the parent env. | files: smoke_098_100.py, tests/test_x_intake_smoke_098_100.py | err: none | commit db5c13c
- item-10-node-version | DONE | tests: before the fix, both node --version tests FAILED (22 PAID_KEYS names, dummy pfy-test-dummy). After clean_env, 103 and 106 modules Ran 16 tests OK. Mutation: pass os.environ from both node_major functions and both tests FAILED the same way. Restored. The version probe uses its own pfy-node-ver- temp HOME. | files: smoke_103_105.py, smoke_106_108.py, two test modules | err: none | commit 3ff882a
- item-11-brigade-bwrap | DONE | tests: before the receipt move, the timeout test updated pipelines/smoke/brigade/latest.json (mtime changed; porcelain stayed empty because the dir is ignored). After, the module Ran 4 tests OK and the repo tree signature was unchanged. No-bwrap PATH: exit 0, containment real-home-snapshot, real_home_state_unchanged true. Fake bwrap: wrapped argv contains --unshare-pid and containment bwrap-ro-root-no-net. Mutation: drop --unshare-pid and both flag tests FAILED (containment fell back; probe log had no --unshare-pid). Mutation: ignore PFY_SMOKE_RECEIPT_DIR and the no-bwrap test ERRORed (temp receipt missing). Both restored. No smoke code change. | files: tests/test_x_intake_smoke_109_111.py | err: none | commit 4884e34
- item-12-smolvm-digest | DONE code+test / BLOCKED live | tests: before the parser, both subtests FAILED (image_digest None). After, the stub test OK for alpine and alpine:3.19. Mutation: drop the assignment and both subtests FAILED (exit 1, reason names the missing digest). Restored. Live: ~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm absent, so the nimo machine run was not started. /dev/kvm is read/write. Nothing downloaded. | files: smoke_109_111.py, test_x_intake_smoke_109_111.py, 109-smolvm.md, x-intake-2026-10-11-handoff.md | err: none | commit faa62e6

## Local CI

Every distinct `run:` step of `.github/workflows/eval-structural.yml`, once (the two jobs repeat structural, golden, jev selftest, unittest, and catalog_check). All RC 0.
- structural, golden, gab selftest, jev selftest, launch-wizard selftest, jev cua-s1-forms smoke: RC 0
- unittest: Ran 367 tests in 101.586s OK (skipped=4) exit 0
- catalog_check, catalog_dashboard, smoke_contract_lint, check_no_encoded_payloads selftest and check, pfy toolset matrix, pfy toolset plan jev, pfy hedge decide, launcher file checks, pfy help: RC 0
- Restored `pipelines/eval/golden.latest.md` (timestamp only) and `pipelines/catalog/dashboard.latest.md` (regenerated n=7 vs committed n=48). Not part of this drop-in. `structural.latest.md` did not change.

## Exit

STOPPED_EXIT: none. Exit: DONE. Skip streak 0. No STOP file. Wall clock from 2026-10-17T12:24:43-07:00, finished the same afternoon, under the 6h cap.
Code head: faa62e6. Handoff commit: 4c673ac. The stamp commit (child of 4c673ac) is the branch tip.

## Fix round 1

Start: 2026-10-17T14:15:23-07:00
Host: nimo
Worktree: /home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups
Branch: build/pr284-followups
Head at start: b7cdb77 (drop-in on 31bc2f0). Base stays origin/main 0d574f0. No merge, no rebase.
Remote: origin/build/pr284-followups is b7cdb77. No other branch already solved the pinned-ref digest.

Overview: Tester FAILED at 31bc2f0 on the smolvm image digest (blocker) plus four follow-ups. Fix each item on this worktree, prove RED with the named mutation, one commit and one push per item, then record counts and the handoff.

Phases:
- baseline | tests/ | `python3 -m unittest discover -s tests -t .` on the unmodified tree. Record Ran/OK/skips. Red base stops the run. | none | general
- item-1-smolvm-pin | examples/x-intake-local/smoke_109_111.py, tests/test_x_intake_smoke_109_111.py, sources/entries/109-smolvm.md | Digest comes from the pinned ref (default alpine 3.22 index, or a digest-pinned $SMOLVM_IMAGE). Evidence is Pulling image or a cache line. PFY_SMOLVM_KVM_PATH lets tests reach machine run. Tests a-f green. Mutations: output digest -> (d) red; drop pin check -> (c) red; drop evidence FAIL -> (e) red. Live run only if the binary exists. | baseline | general
- item-2-receipt-dir | tests/test_x_intake_smoke_112_114.py, tests/test_x_intake_smoke_115_116.py | Every smoke run uses PFY_SMOKE_RECEIPT_DIR. gitignore checks do not leave files. A snapshot of `git status --porcelain --ignored pipelines/smoke` is unchanged after both modules. Mutation: drop the env from one test -> snapshot red. | item-1 | general
- item-3-timeout-step | examples/x-intake-local/smoke.py and every timeout_reason caller, README, the asserting tests | timeout_reason(step, seconds) returns `{step} timeout after {seconds:g}s`. Sponsio plus one 112 and one 115 test assert step and seconds. Mutation: ignore step -> those tests red. | item-2 | general
- item-4-scrub-env | examples/x-intake-local/smoke.py, smoke_103_105.py, smoke_106_108.py, their tests | scrub_env drops PAID_KEYS and SECRET_ENV_RE. node --version gets PATH, LANG, LC_ALL, TMPDIR, and the temp HOME. Stub node sees none of the dummy tokens. Mutation: clean_env from os.environ without scrub_env -> red. | item-3 | general
- item-5-handoff-counts | docs/ops/HANDOFF-pr284-followups-2026-10-17.md | skipped=4 lines name nimo. Tester skipped=6 (KVM and toolchain) is stated. No code change. | item-4 | general
- finish | this log, the handoff, AUTONOMOUS-DECISIONS | Final suite, local CI run: steps, handoff section, commit `docs: fix1 handoff`, push. | all items | general

Risks:
- Baseline red stops before item 1 (BLOCKED: red-base).
- One full suite at a time. Item tests are single modules.
- Mutations are restored before any commit. A mutated tree is never pushed.
- Live smolvm stays BLOCKED when ~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm is absent. Nothing is downloaded.
- Wall clock: no new item after 15:00 local (45 minutes from 14:15:23). Finish by about 15:10. Commit and push after every item.
- Phases share this one worktree and smoke.py, so they run in order here. No extra worktree.

## Fix round 1 baseline

`python3 -m unittest discover -s tests -t .` on nimo, unmodified tree at b7cdb77.
Result: Ran 367 tests in 101.620s OK (skipped=4) exit 0.
No red base.

## Fix round 1 items

- item-1-smolvm-pin | DONE code+test / BLOCKED live | tests: tests.test_x_intake_smoke_109_111 Ran 10 tests in 3.055s OK. RED: record digest from output again -> test_d_smolvm_guest_sha_is_not_the_digest FAILED (failures=1). RED: drop the pinned-ref check -> test_c_smolvm_unpinned_env_exits_2 FAILED (failures=1, IndexError on an unpinned ref). RED: remove the evidence FAIL -> test_e_smolvm_missing_evidence_exits_1 FAILED (failures=1). Each restored and that test OK. Live: ~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm absent, so the nimo machine run was not started. /dev/kvm is read/write. Nothing downloaded. | files: smoke_109_111.py, test_x_intake_smoke_109_111.py, 109-smolvm.md | err: none | commit f3dfc9d
- item-2-receipt-dir | DONE | tests: 112 and 115 modules Ran 12 tests in 11.569s OK. Snapshot test Ran 1 test OK. RED: drop PFY_SMOKE_RECEIPT_DIR from 112 _parent_env -> test_both_modules_leave_pipelines_smoke_unchanged FAILED (failures=1, file snapshot changed). Restored, Ran 1 test OK. | files: test_x_intake_smoke_112_114.py, test_x_intake_smoke_115_116.py, test_x_intake_smoke_112_115_receipts.py | err: none | commit d2d9d1f
- item-3-timeout-step | DONE | tests: sponsio, overtime, festival, daemon-stop, openqodex, harnessrouter cleanup, brigade timeout, 117 module, agentdescent timeout OK. RED: timeout_reason ignores step -> sponsio, overtime, and openqodex FAILED (failures=3). Restored, those 3 OK. Grep of examples/x-intake-local for a hand-written timeout sentence: only the helper return and the README. | files: smoke.py and every caller, README, four test modules | err: none | commit 85e499a
- item-4-scrub-env | DONE | tests: tests.test_x_intake_smoke_103_105 and tests.test_x_intake_smoke_106_108 Ran 16 tests in 2.192s OK. RED: pass os.environ-derived env (dict(os.environ, HOME=home)) without scrub_env / node_version_env -> test_node_version_uses_clean_env in 103 and 106 FAILED (failures=2). Restored, those 2 OK in 0.627s. | files: smoke.py, smoke_103_105.py, smoke_106_108.py, two test modules | err: none | commit 209d411
- item-5-handoff-counts | DONE | tests: none (docs only). skipped=4 lines in the handoff now name nimo. This run's nimo baseline is Ran 367 tests in 101.620s OK (skipped=4). Tester's box at 31bc2f0 saw skipped=6 because of KVM and toolchain. The nimo final full-suite count is written in the Fix round 1 handoff section after that suite. | files: HANDOFF-pr284-followups-2026-10-17.md | err: none | commit 537892a

## Fix round 1 finish

Full suite on nimo, after item 5, host free of the runner: `python3 -m unittest discover -s tests -t .`
Result: Ran 373 tests in 113.832s OK (skipped=4) exit 0.

Local CI, each distinct `run:` step once. All RC 0 after the structural rerun.
- structural first attempt RC 1: pfylib_unittests FAILED (failures=1, skipped=4) on test_module_run_leaves_no_new_tmp_dirs while the self-hosted runner was also running unittest. Discarded.
- structural rerun, host free: STRUCTURAL EVAL PASS. Embedded suite Ran 373 tests in 113.526s OK (skipped=4). RC 0.
- golden, gab selftest, jev selftest, launch-wizard selftest, jev cua-s1-forms, catalog_dashboard, catalog_check, smoke_contract_lint, check_no_encoded_payloads selftest and check, pfy toolset matrix, pfy toolset plan jev, pfy hedge decide, launcher file checks, pfy help: RC 0.
- Restored pipelines/eval/golden.latest.md (timestamp) and pipelines/catalog/dashboard.latest.md (regenerated). structural.latest.md is gitignored.

## Fix round 1 exit

STOPPED_EXIT: none. Exit: DONE. Skip streak 0. No STOP file. Item 1 not skipped.
Wall clock from 2026-10-17T14:15:23-07:00. Finished the same afternoon, under the 55 minute finish line.
Live smolvm: BLOCKED (binary absent at ~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm). /dev/kvm is read/write. Nothing downloaded.
Final head: the docs: fix1 handoff commit, parent 537892a.
