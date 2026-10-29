# Handoff: local pregate check

## Status

Branch `bot/pregate-check`, fix round 2 after Tester FAILed `6164cc6` (B4) and Reviewer filed F2 to F7. `origin/main` `8430e90` (x148 bwrap fix) is merged in. Not merged to main, and no gates requested by the implementer. Results for the pinned SHA are under "Verify" below.

## Goal

A free local pre-gate on nimo, so that branches catch known failure classes before Tester/Reviewer gate rounds. Past gate rounds failed on unsandboxed tests, red ubuntu CI, test-runner cheats and orphan processes.

## What landed

| path | role |
|---|---|
| `scripts/pregate.sh` | Driver: isolated short-path worktree, seven checks, persisted logs and summary, nonzero exit on FAIL |
| `docs/ops/PREGATE.md` | How to run, output paths, check table, rule: attach the summary before any gate request |
| `docs/ops/HANDOFF-pregate.md` | This handoff |

No unit tests were added for pregate itself. It is verified by running it against known-good and known-bad commits (below).

## Fix round 1 (gate findings on 172f5df)

Tester blockers:

- B1, typo false PASS: `--only` validates names (comma list) and exits 2 on an unknown one. Overall is FAIL when no check passed.
- B2, logs deleted: logs, receipts and the summary are written to `~/DEVELOP/pfy-mentat/tmp/pregate-runs/<run-id>/`, which cleanup never removes. Every FAIL line points there.
- B3, bwrap-less false pass: new `ubuntu-parity` check runs the full discover with bwrap hidden. The PATH is now a mirror of the caller's PATH minus `bwrap`, not a hand-picked list. The PREGATE.md mapping is corrected.

Reviewer blockers:

- RB1: G0 receipts go to the run folder (`receipts/`), so `--in-place` no longer rewrites tracked `pipelines/eval/*.latest.md`.
- RB2: the next-steps section below uses the no-PR flow.
- RB3: no em or en dashes in the added files, including the generated summary lines.

Should-fix items folded in:

- Fail closed: the orphan check FAILs if `ps` fails. The orphan check also diffs a before/after process snapshot and matches on cwd as well as argv.
- Preflight: run root and scratch must be 60 characters or less (exit 2 otherwise). Whitespace in the repo path exits 2. A bad ref exits 2, and `--only` with no value exits 2.
- Signals: SIGINT/SIGTERM/SIGHUP stop only this run's own descendants, write a FAIL summary and clean up. Checks run in the background with `wait`, so the trap fires promptly.
- Watchdog per check (`PREGATE_STEP_TIMEOUT`, default 2400 s): a hung step is killed and reported.
- Stale runs: each run writes `tmp/pg/.owner-<name>` with its pid. The next run prunes worktrees whose owner is no longer a live pregate (the SIGKILL case).
- TMPDIR: when the repo is under `/workspace/*`, the caller's TMPDIR is kept, because pregate's own TMPDIR there false-fails `test_lab_stage`.
- gate-hash: walks the HEAD tree, so a deleted or renamed (including staged rename) test is reported, not a crash. It also diffs committed changes vs the merge-base with `--base` (default `origin/main`): a strict gate file added/changed/deleted in a commit FAILs, and edited existing tests are listed as NOTEs. This closes most of the "tautological in worktree mode" gap.
- ci-parity: a missing test file now FAILs, and comments no longer satisfy the static pin.
- Removed: the unused STAMP variable, the stale "suite owns discover" comment and the unsourced weekly-usage figure. The summary notes that skip counts depend on the host.

## Fix round 2 (gate findings on 6164cc6)

- B4: an unresolvable `--base` exits 2 before any check (it used to skip the committed gate-file diff and PASS). gate-hash also FAILs if the base SHA is somehow missing.
- PID reuse (Tester, Reviewer F4): `kill_tree` signals a PID only while it is still a direct child of this pregate, checked before TERM and again before KILL. A watchdog left behind by a SIGKILLed pregate finds its child reparented and does nothing.
- Owner files: only `.owner-<7 hex>-<6 digits>` names are used; anything else (for example `.owner-..`) is ignored with a message, never removed.
- More than one positional REF exits 2 (F6).
- The summary says "no check ran to completion" only when nothing passed and nothing failed.
- The prune message distinguishes "owner pid is gone" from "owner pid is alive but is not a pregate (pid reused)".
- PREGATE.md documents the whitespace-path refusal, one pregate per host and the unknown-base exit.
- Retention: the newest 20 run folders are kept (`PREGATE_KEEP_RUNS`); only run-id-named folders in `tmp/pregate-runs/` are pruned.
- Usage (`--help`) prints only the header comment, not the `set -euo pipefail` line (F5).
- This handoff: Isolation wording corrected (F2) and Verify rows marked by the code they ran on (F7).

## Verify

```bash
./scripts/pregate.sh <pinned sha>          # expect OVERALL=PASS
./scripts/pregate.sh --only ci-parity 2fadea1   # expect FAIL (runtime-dir tests lack auto_unsafe=False)
./scripts/pregate.sh --only lnt            # expect exit 2
```

Round 1 results. The "code" column says which pregate code ran: `412e970` or `pre-412e970` (the uncommitted working copy before that commit, F7). Round 2 results are further down. Run folders are under `~/DEVELOP/pfy-mentat/tmp/pregate-runs/`. Times are PDT, 2026-10-29.

| code | run | expected | result | run folder |
|---|---|---|---|---|
| 412e970 | full, `412e970` (tip) | PASS once main is green | FAIL, rc 1, 1060 s: only ubuntu-parity fails (10 failures, all `tests.test_x_intake_smoke_148`, "bwrap is not usable here"); lint, ci-parity, gate-hash, eval-structural, orphans PASS | `412e970-20261029T084456Z-3441835` |
| 412e970 | full, `997d892` (ubuntu CI green) | PASS | PASS, rc 0, 1060 s, ubuntu-parity included | `997d892-20261029T090236Z-3563052` |
| 412e970 | `--only ci-parity 2fadea1` | FAIL | FAIL, rc 1, 8 s | `2fadea1-20261029T092016Z-3666349` |
| 412e970 | `--only ubuntu-parity` on `4b85eb0` (local probe: 997d892 plus a 129bc85-style test that needs bwrap) | FAIL | FAIL, rc 1, 437 s, exactly 1 failure: `test_needs_bwrap` | `4b85eb0-20261029T084456Z-3441834` |
| 412e970 | `--only lnt` | exit 2 | exit 2, "unknown check 'lnt'" | none |
| pre-412e970 | `--only` with no value, bad SHA `deadbeef1234` | exit 2 | exit 2 | none |
| pre-412e970 | gate-hash with a staged rename and a deleted test (`--in-place --allow-dirty`) | FAIL, no crash | FAIL listing the deleted, renamed and new paths | `fc3561e-20261029T084404Z-3429275` |
| pre-412e970 | gate-hash on a local commit adding `conftest.py` and weakening an assert | FAIL plus review note | FAIL "committed A of gate file", NOTE for the edited test | `20fba52-20261029T084410Z-3433679` |
| pre-412e970 | SIGTERM mid-run | rc 143, FAIL summary, own children stopped | as expected, worktree removed | `997d892-20261029T084138Z-*` |
| pre-412e970 | SIGKILL, then next run | stale worktree pruned only once its processes are gone | pruned with "owner pid ... is gone" | none |

Tip FAIL is a real regression on main, not a pregate false positive: `3278cfc` added `tests/test_x_intake_smoke_148.py`, which needs bwrap, and GitHub "G0 (ubuntu-latest)" on `3278cfc` concluded failure (run 40835727021) while "G0 (self-hosted nimo)" passed. The tip goes green when the x148 owner fixes or skips that test without bwrap. This branch does not touch product tests. Fixed on main by `8430e90` (`bot/fix-x148-bwrap`), now merged here.

ROUND2_PLACEHOLDER

## Dates (America/Los_Angeles)

- 2026-10-28, evening: first version built. Full run on 997d892 PASSed (613 s), finishing about 23:57 PDT.
- 2026-10-29, about 00:15 PDT: `172f5df` pushed.
- 2026-10-29, about 00:20 to 01:10 PDT: Tester and Reviewer gated `172f5df`, both FAIL.
- 2026-10-29, from about 01:15 PDT: fix round 1 (this file).
- 2026-10-29, about 02:22 PDT: `6164cc6` pushed; Tester FAILed it on B4.
- 2026-10-29, from about 03:18 PDT: fix round 2; `origin/main` `8430e90` merged in.

## Known gaps

- Python version and missing tools are not emulated: CI uses 3.12, while nimo uses the host python3. grok/Ollama absence on ubuntu is not simulated either.
- ubuntu-parity hides bwrap entirely. An ubuntu runner where bwrap exists but user namespaces are blocked could behave differently.
- The orphan check only sees processes whose argv or cwd is under this run's paths. A daemon that `chdir`s elsewhere and has no path in its argv is missed.
- The watchdog stops pregate's own descendants. An orphan that has re-parented away is reported by the orphan check but never signalled.
- A gate-file change in a commit FAILs gate-hash on purpose. A branch that legitimately edits `pyproject.toml` or similar needs a reviewer waiver.
- `tmp/pregate-latest-summary.md` is overwritten by whichever run finishes last. Attach the run-folder copy.
- Retention keeps 20 run folders, so evidence folders cited below can age out; copy a summary elsewhere to keep it.
- A full run is about two discovers long (see Verify). Use `--only` for fast loops, but never attach a partial summary to a gate request.
- One pregate per host: concurrent runs are not coordinated.
- `eval-structural.yml` is not triggered from here. This is local reproduction only.

## Isolation

Work happened in `~/DEVELOP/pfy-mentat/tmp/pgfix` on `bot/pregate-check`. Pregate is not invisible to the main checkout: its run worktrees (`tmp/pg/`), scratch (`tmp/pgs/`), run folders (`tmp/pregate-runs/`) and `tmp/pregate-latest-summary.md` live under the main checkout's gitignored `tmp/`, each run registers a worktree in the shared `.git/worktrees/`, and some tests write under the shared `.git` (for example `.git/opencode`). Tracked files in Mark's main checkout, `tmp/mvp2` and `tmp/x148` were not edited, and no processes other than pregate's own were signalled.

## Next (no-PR flow)

1. Bots gate the pinned SHA: Tester, then Reviewer, each against the summary from a full pregate run on that SHA.
2. When both PASS, fast-forward `main` to the pinned SHA. There is no PR, and the implementer does not merge or request gates.
3. After that, `docs/ops/PREGATE.md` is the standing gate hygiene: a full run and an attached summary before every gate request.
