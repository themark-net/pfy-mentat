# fix: x-intake smoke isolation, honest atg stage, TODO and parity notes

Not a Feature GO. Do not merge until a separate Tester and a separate Reviewer both PASS at the exact head SHA in `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md`.

## Summary

- x-intake smokes for sponsio and repoharness run their tool subprocesses with a fresh temp `HOME`. Opensteps `hook()` and repoharness `hj()` turn `TimeoutExpired` into exit 1 and a receipt reason that contains `timeout`.
- `harness-linux-x64` for `harness-v0.1.10` is pinned to the full sha256 `68b6a51e40cd8e229f1f056c2aa5ea93de7934f746dcf8dd38e3b7d9dd4ee397` from the public release `.sha256` asset. A mismatch exits 2 before the binary runs.
- Smoke receipts under `pipelines/smoke/{sponsio,opensteps,repoharness}/` are gitignored. `pipelines/smoke/kolibri1/latest.json` stays tracked.
- Agent-substrate Stage A commands create the runsc bundle before run, checkpoint, and restore.
- atg-compile bench no longer writes a constant `integration_stage` of `I1`. Absent `--integration-stage` writes `unscored`. Committed receipts are unchanged. No live model.
- TODO GitHub-issues table keeps one done row each for T-0075 and T-0007. The stray block above the title is gone.
- T-0076: skill cross-links to mattpocock `to-spec` and `tdd`. Refs #6. Issue not closed.
- T-0040: Claude Code parity notes from the existing adapter, attach #221, and tests. Refs #8. Issue not closed.

Catalog HOLD 070–075, eval-harness, and issue #76 are untouched.

## Test plan

- [ ] `python3 -m unittest discover -s tests -t .` (this run: 190 OK, skipped=4; baseline was 184 OK, skipped=4)
- [ ] `make eval-structural` (PASS)
- [ ] `python3 scripts/catalog_check.py` (PASS n_json=7)
- [ ] `make smoke-grok-skills` (PASS)
- [ ] x-intake HOME, timeout, and sha256 tests fail on the old smoke and pass after (recorded under `/tmp/orch-decisions-1009/xintake-red.txt` and `xintake-green.txt`)
- [ ] atg cannot-run JSON asserts `unscored` by default and copies `--integration-stage` (red: `'I1' != 'unscored'`)
- [ ] `git status --porcelain pipelines/smoke` empty; kolibri1 receipt still tracked

## Decisions

11 lines: `docs/ops/AUTONOMOUS-DECISIONS-2026-10-09.md`

Refs #6
Refs #8
