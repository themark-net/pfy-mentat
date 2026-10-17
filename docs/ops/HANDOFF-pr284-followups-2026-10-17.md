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

- Baseline, before any item edit: Ran 350 tests in 45.371s OK (skipped=4), exit 0. `tests.test_hedge.DetectorTests.test_detector_runs_offline` did not fail here.
- After item 8 (full suite, before/after `/tmp` diff empty): Ran 360 tests in 97.942s OK (skipped=4).
- Final local CI unittest: Ran 367 tests in 101.586s OK (skipped=4), exit 0.

## Items

| Item | Status | Commit | Notes |
|------|--------|--------|-------|
| 1 SHA WARN | DONE | `8029a82` | WARN only when a sha override differs (case-insensitive). Mutation: drop the equality check, equal-pin tests red. |
| 2 timeout text | DONE | `2d51881` | Every recorded reason is `timeout_reason(tag)`. Sponsio test drives `PFY_XINTAKE_TIMEOUT`. Mutation of the helper text went red. |
| 3 Stage A commands | DONE | `9e4061f` | Blocks use `$STAGE_A` and `$RUNSC`. Checked with a stub runsc under `/tmp`. |
| 4 handoff counts | DONE | `ca4dc7e` | a5c0362 rerun: Ran 191 tests in 5.479s OK (skipped=4). fb3beb5 rerun: Ran 190 tests in 3.953s OK (skipped=4), 2026-10-10 sentence kept. |
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
