# Handoff: harness2-local (2026-10-19 name, run 2026-10-20)

Branch: `bot/h1-harness2`
Base: `aed526d080114f83fbd9ad329b4c9e5b62baf64c` (launch `origin/main`). `origin/main` at `4641585` was merged in at `6f7a620` (no rebase, no force-push).
Head: the CI-fix commit on top of `d8b92fd` (Reviewer B1 at `d8b92fd`: lazy harness2 import in `pfy_adapter.py`, bwrap and staged-harness2 skip guards, long AF_UNIX paths bound through an `O_PATH` dir fd; nits n1 n2 n6 n8, mutant tests n3 n4 n5, Tester N06 N03 N09 N08 tests and a named `--runs`/`--state` under /tmp or /run refusal; this line). The gate request names that pushed SHA. Earlier heads: `d8b92fd` (Reviewer nits N1 N3 N4 N6), handoff commit `c6fe837`.
Gate status: ready for Tester and Reviewer at the pushed SHA. `902e04f` was FAIL before item 2c. Compare: https://github.com/themark-net/pfy-mentat/compare/main...bot/h1-harness2
Proposal branch: none. `git ls-remote --heads origin 'bot/h2-proposal-20261020*'` was empty.
Exit: goal met (H1c, 2026-10-20 15:34 PDT). The H1b stop-file was an intentional pause so item 2c could run first. It is not this session's exit.

## Status

| Item | Status |
|------|--------|
| 0 drop-in | ALREADY-DONE |
| 1 stage | DONE |
| 2 sandbox | DONE. N1, N2, N5 PASS |
| 2b fixes | DONE |
| 2c fixes | DONE. Full suite 520 OK (skipped=4) at that commit |
| 3 adapter | DONE. `3260e0228cee5344578bfad2a26076ef43bb03ec` |
| 4 surface | DONE. `475f34ddc8736969db253e3ed654fd85f8bbaea1` |
| 5 propose | DONE. `4bd065de7a2366149dac47f4c9cf964e31e65f20` |
| 6 live | DONE. Negative finding: gain 0. Receipt `pipelines/dogfood/harness2-local/receipt.json` (`c26ad1a`). No proposal branch |
| N6 code | DONE. `6f6034616c14e2bce697690c111b263ac3c19204` (`sbun` exec) |
| 7 docs | DONE. Entry 136 is I1, tier C, overall 59. `1b2d907` plus handoff-card fix `31f96ed` |
| N checks | N1 N2 N3 N4 N5 N6 PASS |

## Live receipt

Held-out a1 and a2: 15/16, parse_ok 1.0, wrong-but-confident 1. Chain final (step c): 15/16, same parse_ok, same wrong-but-confident. Gain 0. Gate needs 2. Better base is a1. The only harness change is an empty `LongTermMEMORY.md`. 288 relay POSTs, all temperature 0 and seed 230. Prompt-eval peak 24231. Two calls truncated at n_tokens 32767. Ctx stayed 32768 (D25). Min MemAvailable during scoring 52210068 kB, floor 16777216 kB.

## Tests

- Baseline at `aed526d`: `python3 -m unittest discover -s tests -t .` 459 tests, OK (skipped=4). The two previously known failures passed on nimo and are not allow-listed.
- Earlier, inside structural eval on `31f96ed`: Ran 545 tests in 433.377s, OK (skipped=4).
- At `d8b92fd` on nimo (staged): Ran 609 tests, OK (skipped=4). CI run 39540683605 was red: no staged `tmp/harness2` on either runner, no bwrap on ubuntu-latest, two AF_UNIX paths over 107 bytes in the nimo runner's deeper checkout. The Reviewer's own run of the same head saw 1 failure (`test_hedge`) and 5 skips, so the suite result depends on the host.
- At the CI-fix head on nimo, staged `tmp/harness2` and bwrap: Ran 617 tests in 452.126s, OK (skipped=4). Fresh clone with no staged harness2 (CI-like, deeper path than the nimo runner): Ran 617, OK (skipped=14: 7 harness2 not staged, 2 staged OpenCode, 1 stage venv, 4 pre-existing). Same clone with bwrap removed from PATH (ubuntu-like): Ran 617, OK (skipped=51: 40 bwrap, 6 harness2 not staged, 1 stage venv, 4 pre-existing). `test_hedge` passed on nimo in all three; the Tester and Reviewer box sees it fail on base `4641585` too (pre-existing, host-dependent).
- Structural eval: PASS (wrote `pipelines/eval/structural.latest.md`, gitignored). Golden PASS. `catalog_check` PASS. `catalog_dashboard` PASS. `check_no_encoded_payloads` PASS. The other eval-structural `run:` steps (gab, jev, launch wizard, launcher, toolset, hedge) passed on the 15:09 CI run. The later diff is the handoff card, the "I1 stay" note, and the XDG stub's `answer.json`.

## RED

Item RED lines are in `docs/ops/RUN-LOG-harness2-local.md`. N6: wait instead of exec in `sbun` leaves sandbox.py, the relay, and bwrap alive (`test_sigkill_of_sbun_reaps_the_sandbox`). Restored exec. The test passed. Live N6: proposer `timeout after 12s` with nothing left, executor rc 124, next call swept a mode 000 dir and wrote its marker.

## Server stop

This session's llama-server was pid 425470, pgid 425470, port 127.0.0.1:18111. At 2026-10-20 15:34 PDT the group had only that process. SIGTERM to pgid 425470. The process exited. `GET /health` then failed to connect. `tmp/host-only/llama-watch.stop` was written first. Watcher pid 425489 exited. No `mem-edge.txt`. Not signaled: monerod pid 1163482, node pid 121239, grok pids 103455 and 103456.

## Not a Feature GO

Catalog HOLD 70-75 was not touched. No merge, no PR, no push of `main`.

Decisions: `docs/ops/AUTONOMOUS-DECISIONS-2026-10-19-harness2-local.md`
Run log: `docs/ops/RUN-LOG-harness2-local.md`
