# Handoff: mvp-dogfood4-1031

Branch: `bot/mvp-dogfood4-1031`. Base: `origin/bot/mvp-integrate-1031` at `1dee0b91`. Not merged. No PR. No tag.

Exit: DONE. The exit card turn cap is 8 cloud builds. Planned queue 6/6 accept. Overall 7 accept and 1 reject, pass rate 7/8.

Pregate not run: host busy. `Runner.Worker` was live (pid 1225684 at 2026-11-01T02:14:52Z) and `flock -n` on `~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock` failed. Project map not drawn: dogfood5 and other Grok lanes were still running.

Gate for this branch: Tester plus Reviewer. The commits change runtime (`pfylib` and x-intake smokes) plus tests and receipts. Pregate is not a substitute while the runner is busy.

## Planned six

| n | slug | result | landed | tests |
| --- | --- | --- | --- | --- |
| 01 | toolset-symlink | accept | `d900cc3` | `tests.test_toolset_apply_symlink` `tests.test_toolsets` 29 OK |
| 02 | modules-symlink | accept | `2e8d20e` | `tests.test_loop_paint_symlink` `tests.test_loop_paint` 11 OK |
| 03 | opencode-config-symlink | accept | `d2dc658` | `tests.test_bot_interface_opencode_symlink` `tests.test_bot_interface` 22 OK |
| 04 | hiroute-term-wait | accept | `d507591` | `tests.test_smoke_146_term_wait` 3 OK; `tests.test_x_intake_smoke_146_147` 35 OK |
| 05 | skillup-fixture-digest | accept | `e6aad0d` | digest + term-wait + smoke 146, 41 OK |
| 06 | taste-fixture-digest | accept | `538c771` | `tests.test_smoke_143_site_digest` `tests.test_x_intake_smoke_143_145` 73 OK (1 skipped) |

Planned pass rate: 6/6.

## After the six (turn cap)

| n | slug | result | landed | tests |
| --- | --- | --- | --- | --- |
| 07 | hedge-ledger-symlink | reject, cross-lane, FINDING-D4-01 | none | red gate dropped, not pushed |
| 08 | files-under-symlink | accept | `b74d5c9` | files-under + site digest + smoke 143, 74 OK (1 skipped) |

Overall pass rate: 7/8.

Receipts: `eval/mvp-1031/dogfood4/<n>-<slug>/{command.txt,diff.patch,notes.md,receipt.json}`. Product authors stay `pfy-cloud-build`. Each accept adds a `Built-by` trailer only.

## Fail and recover

01. Fail: write, append-marker, and json-merge on an in-root symlink replace the symlink and leave the target bytes. Recover: a regular file still updates. An outside-resolving symlink stays refused.

02. Fail: `load_selection` does not read a symlink, and `save_selection` replaces it. A broken symlink does not create the missing target. Recover: a regular `loop-modules.json` still round-trips.

03. Fail: `write_opencode_config` replaces a symlink at `opencode.json` and does not create a broken symlink's target. Recover: a regular file still receives the provider JSON.

04. Fail: `abc`, `0`, `-1`, `nan`, `inf`, and `601` exit 2 with a reason that names `HIROUTE_TERM_WAIT` and does not say the archive is not staged. Recover: unset, empty, whitespace-only, `10`, `600`, and a padded `10` still reach the staging miss. skill-up ignores the variable.

05. Fail: a byte edit changes `fixture_digest`. A same-bytes symlink also changes it, and a missing target does not raise. Recover: restoring the original bytes restores the digest. The skill-up stub suite still passes.

06. Fail: a symlink whose target bytes match the regular file changes `site_digest`, and a missing target does not raise. Recover: a regular site tree still digests from file bytes.

07. Not landed. The cloud diff was one file and the gate went green. It duplicates `origin/bot/mvp-selfhost2-1031` `3eeab42`.

08. Fail: `files_under` omits a symlink and leaves the target bytes. Recover: a regular file in the same directory is still listed.

## Skipped before item 01

TODO rows that need a shelf, a local model, docker, a parked env, hardware, an ADR, or an open OQ: T-0091, T-0094, T-0081, T-0064, T-0043, T-0062, T-0046, T-0016, T-0005. `docs/TODO.md` was not edited.

dogfood3's five accepts and its rejected smoke_137. Other smokes that still swallow a bad timeout, because those files sit on other bot branches.

dogfood5's FINDING list. `scripts/pfy_build_cloud.py`, `scripts/pfy_build_local.py`, `scripts/pfy`, `scripts/pregate.sh`, and `examples/local-bench/`. smoke_149 content cap (needs a written size limit, and other lanes own the file). `smoke_140_142.py` `tree_hash` (selfhost2).

## Cross-lane

FINDING-D4-01: do not edit `pfylib/hedge.py` on this branch. selfhost2 `3eeab42` already replaces the ledger symlink. The cloud commit `d96b811` stays on the throwaway branch `cloud/edit-only-pfylib-hedge-py-do-not-edit-an-20261101T020951530246Z` inside the removed clone. No request for them to change course.

Not taken, left for a later lane after an ownership check: `pfylib/attach.py` and `pfylib/hermes_bot_driver.py` still call `write_text` on paths that can be symlinks. The turn cap stopped this lane first.

## Next step

Review this branch (Tester plus Reviewer). Do not merge it from this lane. Do not start another `./pfy build` here. When the runner is idle and the heavy lock is free, pregate can run once.
