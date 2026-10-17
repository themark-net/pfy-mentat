# Handoff — pr284-followups — 2026-10-17

Exit: DONE.

Branch: `build/pr284-followups`
Base: `origin/main` `0d574f0649ccfe5bdd5d5384786c74173fb6e41e`
Code head (item 12): `faa62e6`
Handoff commit: `4c673ac579a2e5bff3188f26aa415ec15151cffa`
Final head: the stamp commit whose parent is `4c673ac` (this line is the only change in that commit).
Compare: https://github.com/themark-net/pfy-mentat/compare/main...build/pr284-followups
No pull request.

## Counts

- Baseline, before any item edit, on nimo: Ran 350 tests in 45.371s OK (skipped=4), exit 0. `tests.test_hedge.DetectorTests.test_detector_runs_offline` did not fail here.
- After item 8 (full suite on nimo, before/after `/tmp` diff empty): Ran 360 tests in 97.942s OK (skipped=4).
- Final local CI unittest on nimo: Ran 367 tests in 101.586s OK (skipped=4), exit 0.
- Fix round 1 baseline on nimo, at `b7cdb77`: Ran 367 tests in 101.620s OK (skipped=4), exit 0.
- Fix round 1 final full suite on nimo: Ran 373 tests in 113.832s OK (skipped=4), exit 0.
- Tester's box, review of `31bc2f0`: skipped=6 because of KVM and toolchain.

## Items

| Item | Status | Commit | Notes |
|------|--------|--------|-------|
| 1 SHA WARN | DONE | `8029a82` | WARN only when a sha override differs (case-insensitive). Mutation: drop the equality check, equal-pin tests red. |
| 2 timeout text | DONE | `2d51881` | Every recorded reason is `timeout_reason(tag)`. Sponsio test drives `PFY_XINTAKE_TIMEOUT`. Mutation of the helper text went red. |
| 3 Stage A commands | DONE | `9e4061f` | Blocks use `$STAGE_A` and `$RUNSC`. Checked with a stub runsc under `/tmp`. |
| 4 handoff counts | DONE | `ca4dc7e` | a5c0362 rerun on nimo: Ran 191 tests in 5.479s OK (skipped=4). fb3beb5 rerun on nimo: Ran 190 tests in 3.953s OK (skipped=4), 2026-10-10 sentence kept. |
| 5 gitignore 103-111 | DONE | `598c602` | Dirs already ignored. New test. Mutation of the smolvm ignore line showed `?? pipelines/smoke/smolvm/`. kolibri1 stays tracked. |
| 6 graphjin log | DONE | `12733a3` | Closes already in `graphjin_world`. Tests lock Popen-raise and early-exit under ResourceWarning. Mutation of each `log.close()` went red. |
| 7 XDG and work dir | DONE | `11511a5` | `clean_env` already set the four dirs. New rulora and cass tests. Har outside-HOME test already on main. Mutation: drop the four dirs, KeyError. |
| 8 tmp cleanup | DONE | `c6ec88a` | Extended prefixes. Mutation: drop cli `addCleanup`, 13 `pfylib-cli-*` left behind. Full-suite prefix diff added 0, removed 0. |
| 9 PAID_KEYS | DONE | `db5c13c` | sponsio, opensteps, and repoharness use `smoke.PAID_KEYS`. Dummy `pfy-test-dummy`. Mutation: drop the filter, 22 names leaked. |
| 10 node --version | DONE | `3ff882a` | Both smokes use `clean_env` and a `pfy-node-ver-` HOME. Mutation: `env=os.environ`, both tests red. |
| 11 brigade receipts and bwrap | DONE | `4884e34` | Temp `PFY_SMOKE_RECEIPT_DIR`. No-bwrap is `real-home-snapshot` and PASS when the snapshot is unchanged. `--unshare-pid` is passed; an unsupported probe drops the whole prefix. Mutation: drop the flag, both tests red. Repo `pipelines/smoke` unchanged. |
| 12 smolvm digest | DONE code+test, BLOCKED live | `faa62e6` | Receipt records `image` and `image_digest`. Stub covers `alpine` and `$SMOLVM_IMAGE`. Mutation: drop the assignment, exit 1. Live BLOCKED: `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` absent. `/dev/kvm` is read/write. Nothing downloaded. |

Skip streak: 0. No item SKIPPED. No red base.

## Local CI

All distinct `run:` steps of `.github/workflows/eval-structural.yml` exited 0 (structural, golden, gab selftest, jev selftest, launch-wizard selftest, jev `cua-s1-forms` smoke, unittest, catalog_check, catalog_dashboard, smoke_contract_lint, `check_no_encoded_payloads.py` selftest and check, `./pfy toolset matrix`, `./pfy toolset plan jev --harness opencode`, `./pfy hedge decide`, launcher checks, `./pfy help`). The two workflow jobs repeat a few of those; each command ran once.

Restored `pipelines/eval/golden.latest.md` (timestamp only) and `pipelines/catalog/dashboard.latest.md` (regenerated n=7 against a committed n=48). `structural.latest.md` was unchanged.

## Decisions

14 lines in `docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-pr284-followups.md`.

## Exit that fired

Goal met: every item DONE or DONE with the live part BLOCKED, as the drop-in allows for item 12. Not stop-file, not 3-skips, not time-cap, not red-base.

## Fix round 1 after Tester FAIL @ 31bc2f0

Exit: DONE. Item 1 was not skipped.

- 1 smolvm pin | DONE | `f3dfc9d` | `tests.test_x_intake_smoke_109_111` (a–f). RED: output digest -> `test_d_smolvm_guest_sha_is_not_the_digest` FAILED. RED: drop pin check -> `test_c_smolvm_unpinned_env_exits_2` FAILED. RED: drop evidence FAIL -> `test_e_smolvm_missing_evidence_exits_1` FAILED. Live BLOCKED (smolvm not installed on nimo).
- 2 receipts | DONE | `d2d9d1f` | 112, 115, `test_both_modules_leave_pipelines_smoke_unchanged`. RED: drop `PFY_SMOKE_RECEIPT_DIR` from 112 -> snapshot FAILED.
- 3 timeout step | DONE | `85e499a` | `test_b_sponsio_timeout_reason_is_exact`, `test_overtime_timeout_reason_is_shared_text`, `test_timeout_kills_stub_grandchild`. RED: `timeout_reason` ignores step -> those three FAILED.
- 4 scrub env | DONE | `209d411` | `test_node_version_uses_clean_env` in 103 and 106. RED: `os.environ`-derived env without `scrub_env` -> both FAILED.
- 5 handoff counts | DONE | `537892a` | Docs only. `skipped=4` lines name nimo. Tester's box skipped=6 because of KVM and toolchain.
- nimo baseline at `b7cdb77`: Ran 367 tests in 101.620s OK (skipped=4), exit 0.
- nimo final: Ran 373 tests in 113.832s OK (skipped=4), exit 0.
- Local CI on nimo: structural (rerun), golden, gab selftest, jev selftest, launch-wizard selftest, jev cua-s1-forms, catalog_check, catalog_dashboard, smoke_contract_lint, payload selftest and check, toolset matrix, toolset plan jev, hedge decide, launcher checks, `./pfy help`: RC 0. Structural's suite: Ran 373 tests OK (skipped=4). The first structural run overlapped the self-hosted runner and is discarded. Restored `golden.latest.md` and `dashboard.latest.md`.
- Live smolvm: BLOCKED (smolvm not installed on nimo). `/dev/kvm` is read/write. Nothing downloaded.
- Exit that fired: DONE (goal met). Not stop-file, not time-cap, not red-base.
- Final head: the `docs: fix1 handoff` commit on `build/pr284-followups` (parent `537892a`).

## Fix round 2 after Tester FAIL @ c4bee82

Exit: DONE. Item 1 was not skipped.

- 1 smolvm stub | DONE | `910e8e1` | `test_a_smolvm_default_pin`, `test_f_smolvm_plain_runs_pull_every_time`, `test_g_smolvm_wrong_ref_exits_1`, `test_h_oci_cache_stdout_branch` (b–e kept). RED: M19a -> a, b, d, f FAILED. RED: M21 -> g FAILED. RED: M19b -> h FAILED. (a) and (f) assert `Pulling image <pin>...` (opening eprint). `... done.` skipped: splitlines breaks on CR (decisions log).
- 2 tool-child scrub | DONE | `82d2b1c` | `test_graphjin_child_drops_secret_shaped_env`, `test_cassmemory_child_drops_secret_shaped_env`. RED: M26 -> both FAILED. RED: M28 -> both FAILED on GITHUB_PAT.
- 3 scrub helpers | DONE | `afcb366` | `test_i_smolvm_child_drops_secret_shaped_env`, `test_f_sponsio_child_drops_secret_shaped_env`. RED: 109 PAID_KEYS-only -> test_i FAILED. RED: 098 PAID_KEYS-only -> test_f FAILED.
- nimo baseline at `38b11a3`: Ran 373 tests in 113.543s OK (skipped=4), exit 0.
- nimo final: Ran 379 tests in 116.156s OK (skipped=4), exit 0. Two earlier runs failed only `test_module_run_leaves_no_new_tmp_dirs` while the self-hosted runner was also in unittest; discarded.
- Local CI on nimo: structural (host free) STRUCTURAL EVAL PASS, embedded suite Ran 379 OK (skipped=4). golden, gab, jev selftest, launch-wizard, jev cua-s1-forms, catalog_check, catalog_dashboard, smoke_contract_lint, payload selftest and check, toolset matrix, toolset plan jev, hedge decide, launcher checks, `./pfy help`: RC 0. Restored `golden.latest.md` and `dashboard.latest.md`.
- Live smolvm: BLOCKED (not installed on nimo). `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` absent. Nothing downloaded.
- Exit that fired: DONE (goal met). Not stop-file, not time-cap, not red-base.
- Deferred follow-ups (not done in this PR):
  1. timeouts in 112 overtime main, festival and 115 openqodex name the entry, not the sub-step (`new`, …);
  2. overtime still PASSes "daemon stopped" when `daemon stop` times out and no `overtimed.lock` exists (this predates the PR);
  3. other smoke tests still write ignored receipts into the repo's `pipelines/smoke` (103_111_receipts writes 9, 117_118 writes 2, 098_100 and 119_121 write 3 each);
  4. the smolvm evidence check also accepts a guest-stdout `Caching image <16hex>` line. Anchoring evidence to stderr `Pulling image <ref>` would close that (low risk; the guest runs the smoke's own script).
- After Build: normal merge of origin/main `7b6054a` (#302, catalog 125-127) as `1cb2e1c`, no conflicts. Full suite on nimo at the merge: Ran 379 tests in 115.438s OK (skipped=4). catalog_check PASS, no_encoded_payloads PASS.
- Independent re-check of the mutants on nimo (bytecode off, restored afterwards): M21 -> test_g FAILED; M19a -> test_a, b, d, f, i FAILED; M26 -> 103 graphjin, 106 cassmemory, 109 test_i, 098 test_f FAILED; M28 -> 103 graphjin and 106 cassmemory FAILED. Unmutated: 42 tests OK.
- Note: Python `splitlines()` also splits on `\r`, so for upstream's redraw stream the recorded `image_evidence` is the first segment, `Pulling image <ref>...`, not `... done.`. The check (needle = `Pulling image <ref>`) is the same either way.
