# Handoff: x148 smoke tests skip cleanly without bwrap

## Status

Branch `bot/fix-x148-bwrap`, cut from `origin/main` `3278cfc`. Not merged, and no gates requested by the implementer. Next step (no-PR flow): bots gate the pinned SHA with Tester and Reviewer, then fast-forward main.

## Problem

`3278cfc` is red on ubuntu CI: "G0 (ubuntu-latest)" failed in run 40835727021 with 10 failures in `tests/test_x_intake_smoke_148.py`, all with reason "bwrap is not usable here". `examples/x-intake-local/smoke_148.py` correctly exits 2 when bwrap is unusable, but 10 tests expected a real scan, so they failed on a host without bwrap.

## Change

Test-only. `tests/test_x_intake_smoke_148.py` loads `smoke_148.bwrap_ok()` (the same probe the smoke runs) and marks the 10 scan tests with `@needs_bwrap`, which skips them with "SKIP: bwrap-missing; confinement was not demonstrated". That is the same guard and message `tests/test_pfy_build_local.py` uses.

Not changed:
- Every assertion is unchanged. With bwrap usable, all 14 tests run and none skip.
- `test_no_bwrap_exits_2`, `test_missing_binary_exit_2`, `test_bad_timeout_exit_2` and `test_version_pin_exit_2` still run on every host, so the no-bwrap exit-2 contract is asserted on ubuntu too.
- `smoke_148.py` itself is untouched.

## Verify

```
python3 -m unittest -v tests.test_x_intake_smoke_148          # with bwrap: 14 ok, 0 skipped
PATH=<PATH mirror without bwrap> python3 -m unittest -v tests.test_x_intake_smoke_148   # 4 ok, 10 skipped
scripts/pregate.sh <sha>    # from bot/pregate-check 6164cc6; full run incl. ubuntu-parity
```

RESULTS_PLACEHOLDER

## Known gaps

- On a host where bwrap should work but silently does not, the scan tests skip instead of failing. The nimo self-hosted G0 job has bwrap, so they still run there.
