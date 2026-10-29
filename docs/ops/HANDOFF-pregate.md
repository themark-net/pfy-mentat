# Handoff: local pregate check

## Status

Pushed on branch `bot/pregate-check` (based on main `997d892`) and not merged. Gates have not been requested. Verified on nimo on 2026-10-29: `997d892` PASS, and `2fadea1` caught by ci-parity. See the results below.

## Goal

Free local pre-gate on nimo so branches catch failures **before** Tester/Reviewer gate bots (~49% of weekly Grok Bot usage). Last MVP needed four gate rounds; failures included unsandboxed tests, red ubuntu CI, test-runner cheats, orphan processes.

## What landed

| path | role |
|---|---|
| `scripts/pregate.sh` | Driver: isolated worktree, six checks, summary + nonzero exit |
| `docs/ops/PREGATE.md` | How to run; rule: attach summary before any gate request |
| `docs/ops/HANDOFF-pregate.md` | This handoff |

No tautological unit tests were added. Pregate itself is the operate-or-FAIL harness.

## Verify (recorded by implementer)

Re-run after pull:

```bash
cd ~/DEVELOP/pfy-mentat/tmp/pregate   # or fresh worktree of bot/pregate-check
./scripts/pregate.sh 997d89264495861a178713ccf7d4447ea828afc4
# expect OVERALL=PASS (or real failures reported)

./scripts/pregate.sh --only ci-parity 2fadea1a23e1c061e9acb69873ad22709f4780c8
# expect FAIL on ci-parity (runtime-dir tests lacked auto_unsafe=False)
```

Recorded on nimo, 2026-10-29 (America/Los_Angeles):

- `./scripts/pregate.sh 997d892`: **PASS** in 613 s. lint PASS, eval-structural PASS (`pfylib_unittests`: 916 tests, OK, skipped=16, 610.9 s), suite SKIP (eval-structural already ran the same discover), ci-parity PASS, orphans PASS, gate-hash PASS.
- `./scripts/pregate.sh --only ci-parity 2fadea1`: **FAIL** in 2 s, which is what we want. The static pin reports that both runtime-dir tests lack `auto_unsafe=False`. The behavioral run with bwrap hidden fails both tests with `AssertionError: 0 != 4 : PASS ok ...`: the test helper auto-added `--unsafe-no-sandbox`, so the runtime-dir guard never fired. This is the same class of failure as the ubuntu CI red.
- `./scripts/pregate.sh --only ci-parity 997d892`: PASS (2 tests OK with bwrap hidden).

Earlier failed attempts, kept so nobody repeats them: nested run dirs such as `tmp/pregate/tmp/pregate-runs/<sha>-<long stamp>` made 35 `test_harness2_local_sandbox.SandboxTests` fail with `socket path too long`. A `TMPDIR` inside the run worktree made `test_local_bench.OutdirPathTests.test_relative_outdir_log_path_safe` fail. Runs now go under `~/DEVELOP/pfy-mentat/tmp/pg/<sha>-<HHMMSS>` (about 51 chars), with scratch and `TMPDIR` under `tmp/pgs/`.

## Gaps / non-goals

- This repo has **no ruff CI job**; “lint” means the real CI lint surface (`smoke_contract_lint`, encoded-payloads, catalog, filemode).
- CI-parity hides bwrap via a curated PATH; it does not emulate every ubuntu-latest difference (Python 3.12 vs host 3.14, missing grok on PATH, Ollama down skips).
- A full run takes about 10 minutes on nimo, and most of that is the unittest discover inside `run_structural.py`. use `--only` / `--skip-full-suite` for fast loops, not for gate attachment.
- Does not trigger `eval-structural.yml` on GitHub (`gh` may be logged out); local reproduction only.
- Does not merge to main or request gates.

## Isolation

Worktree: `~/DEVELOP/pfy-mentat/tmp/pregate` on `bot/pregate-check`. Do not touch Mark’s dirty main checkout or `tmp/mvp2` / other live runs.

## Next for the human

1. Review the branch diff.
2. Open/merge PR when ready (implementer does **not** merge or request Tester/Reviewer).
3. After merge, treat `docs/ops/PREGATE.md` as standing gate hygiene.

## Known gaps (pregate itself)

- The run-root path length is load-bearing. Running the script from a checkout whose git common dir sits deeper than `~/DEVELOP/pfy-mentat` can bring back the harness2 `socket path too long` failures.
- `orphans` only sees leftover processes whose argv names this run's paths, and `orphan*.pid` / heartbeat files. A daemon whose argv shows no path is missed. Processes from other worktrees, such as `tmp/mvp2`, are ignored on purpose and are never signalled.
- `ci-parity` hides bwrap and pins the two runtime-dir tests. It does not run the whole suite without bwrap (that would take about 10 more minutes). It does not test Python 3.12 or the absence of grok or Ollama on ubuntu.
- `gate-hash` compares against the commit being gated. It catches a dirty `--in-place` tree or untracked conftest/sitecustomize/tests. It cannot catch a cheat that is already committed. That still needs a diff review against base.
- The full pregate was not run end to end on `2fadea1`. Only ci-parity was run there.
