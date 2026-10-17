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
- item-8-tmp-cleanup | DONE | tests: extended tests/test_pfylib_tmp_cleanup.py Ran 1 test OK in 47.457s (launcher + x-intake modules, diff empty). Mutation: drop test_cli addCleanup rmtree and the same test FAIL with 13 new /tmp/pfylib-cli-* dirs. Restored and removed those 13 dirs. Full suite before/after diff of the same prefixes plus pfy-build- was empty (added 0, removed 0). Suite: Ran 360 tests in 97.942s OK (skipped=4). Pre-existing /tmp/pfylib-test-* (9060) were left in place. | files: tests/test_pfylib_tmp_cleanup.py | err: none
