# Handoff: local pregate check

## Status

Branch `bot/pregate-check`, fix round 1 after Tester and Reviewer both FAILed `172f5df`. `origin/main` (`3278cfc`) is merged in. Not merged to main, and no gates requested by the implementer. Results for the pinned SHA are under "Verify" below.

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

## Verify

```bash
./scripts/pregate.sh <pinned sha>          # expect OVERALL=PASS
./scripts/pregate.sh --only ci-parity 2fadea1   # expect FAIL (runtime-dir tests lack auto_unsafe=False)
./scripts/pregate.sh --only lnt            # expect exit 2
```

RESULTS_PLACEHOLDER

## Dates (America/Los_Angeles)

- 2026-10-28, evening: first version built. Full run on 997d892 PASSed (613 s), finishing about 23:57 PDT.
- 2026-10-29, about 00:15 PDT: `172f5df` pushed.
- 2026-10-29, about 00:20 to 01:10 PDT: Tester and Reviewer gated `172f5df`, both FAIL.
- 2026-10-29, from about 01:15 PDT: fix round 1 (this file).

## Known gaps

- Python version and missing tools are not emulated: CI uses 3.12, while nimo uses the host python3. grok/Ollama absence on ubuntu is not simulated either.
- ubuntu-parity hides bwrap entirely. An ubuntu runner where bwrap exists but user namespaces are blocked could behave differently.
- The orphan check only sees processes whose argv or cwd is under this run's paths. A daemon that `chdir`s elsewhere and has no path in its argv is missed.
- The watchdog stops pregate's own descendants. An orphan that has re-parented away is reported by the orphan check but never signalled.
- A gate-file change in a commit FAILs gate-hash on purpose. A branch that legitimately edits `pyproject.toml` or similar needs a reviewer waiver.
- `tmp/pregate-latest-summary.md` is overwritten by whichever run finishes last. Attach the run-folder copy.
- Run folders under `tmp/pregate-runs/` are never auto-deleted.
- A full run is about two discovers long (see Verify). Use `--only` for fast loops, but never attach a partial summary to a gate request.
- `eval-structural.yml` is not triggered from here. This is local reproduction only.

## Isolation

Work happened in `~/DEVELOP/pfy-mentat/tmp/pgfix` on `bot/pregate-check`. Mark's main checkout, `tmp/mvp2` and `tmp/x148` were not touched, and no other processes were signalled.

## Next (no-PR flow)

1. Bots gate the pinned SHA: Tester, then Reviewer, each against the summary from a full pregate run on that SHA.
2. When both PASS, fast-forward `main` to the pinned SHA. There is no PR, and the implementer does not merge or request gates.
3. After that, `docs/ops/PREGATE.md` is the standing gate hygiene: a full run and an attached summary before every gate request.
