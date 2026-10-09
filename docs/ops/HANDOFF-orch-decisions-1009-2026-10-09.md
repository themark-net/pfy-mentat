# Handoff — orch-decisions-1009 — 2026-10-09

Not a Feature GO. Catalog HOLD 070–075 untouched. eval-harness untouched. Issue #76 stays closed. Do not merge until a separate Tester and a separate Reviewer both PASS at the exact head SHA below.

**Branch:** `build/orch-decisions-1009`  
**Worktree:** `/home/mark/DEVELOP/pfy-mentat/tmp/orch-decisions-1009`  
**Base:** `origin/main` `8c0b547`  
**Head SHA:** tip of `origin/build/orch-decisions-1009` after this push. A commit cannot contain its own id, so the 40-hex value is the orchestrator final message (`Links: … head <sha>`). Tester and Reviewer PASS at that exact sha. `git rev-parse HEAD` on the branch matches it.  
**Compare:** https://github.com/themark-net/pfy-mentat/compare/main...build/orch-decisions-1009  
**PR:** `gh` is not logged in on this host. Body: [PR-BODY-orch-decisions-1009.md](PR-BODY-orch-decisions-1009.md) and `/tmp/pr-orch-decisions-1009.md`. Do not log in from this run. Do not merge.

## What landed

1. **x-intake HOME isolation.** Sponsio's probe and repoharness harness subprocesses run with `HOME` set to a fresh temp dir. Opensteps hooks already did. Commit `e22878f`.
2. **TimeoutExpired.** Opensteps `hook()` and repoharness `hj()` catch `subprocess.TimeoutExpired`, write a receipt whose reason contains `timeout`, and exit 1 (check failed). No traceback. `PFY_XINTAKE_TIMEOUT` overrides the timeout for tests; defaults stay 60s and 120s.
3. **repository-harness pin.** Full sha256 `68b6a51e40cd8e229f1f056c2aa5ea93de7934f746dcf8dd38e3b7d9dd4ee397` for `harness-linux-x64` at `harness-v0.1.10`, taken from the public `.sha256` asset (curl to `/tmp` only; the binary was not run). Pinned in `smoke_098_100.py`, `examples/x-intake-local/README.md`, `sources/entries/100-repository-harness.md`, and `docs/automation/x-intake-2026-10-07-handoff.md`. A mismatched binary exits 2 with a sha256 reason before exec. `HARNESS_SHA256`, when set, is the expected digest.
4. **Gitignore.** Only `pipelines/smoke/sponsio/`, `pipelines/smoke/opensteps/`, and `pipelines/smoke/repoharness/`. `pipelines/smoke/kolibri1/latest.json` stays tracked.
5. **Agent-substrate commands.** The Stage A block now runs `mkdir b && ./runsc spec -bundle b -- <cmd>` and notes `root.path=/` read-only and `terminal=false` before run, checkpoint, and restore. `runsc` was not executed. Commit `afc6f58`.
6. **atg-compile stage honesty.** `--integration-stage` has no default. Absent writes `unscored` on the cannot-run JSON and the scored receipt. A passed value is copied. Committed receipts were not rewritten. No live model. Commit `c63f746`.
7. **TODO hygiene.** The file starts at `# TODO`. GitHub-issues table has one done row each for T-0075 (#5) and T-0007 (#15). The stray #230 and #228 bullets moved into the Done table. The Active parked T-0007 row (it said todo) was removed.
8. **T-0076 (Refs #6, not closed).** Cross-links in `one-shot`, `agent-loops`, and `prefer-behavior-and-fail-recover-tests` to the existing mattpocock `to-spec` and `tdd` SKILL.md paths. No new scorer. Marked done in TODO.
9. **T-0040 (Refs #8, not closed).** `docs/ops/multi-cli-parity.md` section "Claude Code (adapter T-0104, attach #221)" cites existing repo paths. Marked done. Notes only; no install and no sign-in.

Skipped on purpose: #64 release promotion, #53 epic, #24/#25 model labs, T-0124, T-0081 cage smoke, parked rows.

## Decisions

11 lines in [AUTONOMOUS-DECISIONS-2026-10-09.md](AUTONOMOUS-DECISIONS-2026-10-09.md).

## Tests

| Command | Baseline (`8c0b547`) | Final |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -t .` | Ran 184 tests in 3.172s · OK (skipped=4) · exit 0 | Ran 190 tests in 3.882s · OK (skipped=4) · exit 0 |
| `make eval-structural` | STRUCTURAL EVAL: PASS · exit 0 | STRUCTURAL EVAL: PASS · exit 0 |
| `python3 scripts/catalog_check.py` | PASS n_json=7 · exit 0 | PASS n_json=7 · exit 0 |
| `make smoke-grok-skills` | (included in eval: skills_manifest PASS) | PASS: all first-party skill checks ok · exit 0 |
| `python3 -m unittest tests.test_x_intake_smoke_098_100 -v` | n/a (test added this run) | Ran 5 tests in 0.678s · OK |

Red before the fix, then green:

- x-intake: `/tmp/orch-decisions-1009/xintake-red.txt` — `FAILED (failures=5)`. HOME probes saw the parent HOME; timeout receipts did not contain `timeout`; sha256 mismatch returned 1. Green: 5 OK in 0.672s.
- atg: `/tmp/orch-decisions-1009/atg-red.txt` — `AssertionError: 'I1' != 'unscored'`. Green without `ATG_REPO`: `OK (skipped=2)`. Lead re-ran the fake-server e2e with `ATG_REPO` at pin `543e778` (detached worktree, venv symlink, no model): `OK`.

Gitignore after the x-intake tests: `git status --porcelain pipelines/smoke` empty. `git check-ignore` matches the three new dirs. `git ls-files --error-unmatch pipelines/smoke/kolibri1/latest.json` succeeds. `git check-ignore` on that kolibri path exits 1.

## BLOCKED

None.

## Push

Recorded after `git push -u origin build/orch-decisions-1009`. See the run log for the push result line.
