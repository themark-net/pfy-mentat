# Handoff: Entry 149 (MemPalace) smoke B2 fix and Reviewer follow-ups

Branch: `catalog/x-intake-149`. Date: 2026-10-29 PT. Author: Grok Bot (executor), working in `~/DEVELOP/pfy-mentat/tmp/x149` on nimo.

## Status

Code and tests done; branch pushed. Gate pending (pregate plus Reviewer at the pinned SHA). Not merged; bots fast-forward main to the pinned SHA after the gates.

## Problem

Reviewer B2: `smoke_149.py` fell back to running MemPalace with no sandbox (network reachable, writable root) when bwrap was missing or unusable, and could still exit 0 PASS. Entry 148's rule is that an unconfined run is never a PASS: exit 2 with a recorded reason.

## Change

- `examples/x-intake-local/smoke_149.py`
  - No bwrap or unusable bwrap: exit 2, reason `bwrap is not usable here; MemPalace must run with no network`. There is no unsandboxed path any more; `run()` always wraps in bwrap (`--ro-bind / /`, `--unshare-net`, tmpfs `/dev/shm`, `/proc`, only the smoke's temp dir writable).
  - Test-only `PFY_SMOKE_REAL_HOME_BIND=1` binds the real HOME writable so the real-HOME check can be exercised under bwrap (same knob as Entry 148).
  - Version pin is an exact match: the first `X.Y.Z...` token of `--version` must equal `MEMPALACE_VERSION` (was a substring test, so `3.12.0.1` or `13.12.0` passed).
  - Not-staged reason now names the full path `~/DEVELOP/pfy-mentat/tmp/mempalace/.venv`.
- `tests/test_x_intake_smoke_149.py` (10 to 18 tests)
  - `needs_bwrap` guard loads the smoke's own `bwrap_ok`, like Entry 148; tests that need a real scan skip without it.
  - New: no bwrap exits 2 and the stub never runs (empty PATH); child has no network (loopback listener sees no connect); child root is read-only (write outside the temp dir fails); child gets a temp HOME with the copied model cache; mine exit fails the run; timeout `0` and `-5` exit 2 with reason `bad PFY_XINTAKE_TIMEOUT`; inexact versions exit 2.
  - `test_real_home_write_fails` now runs under bwrap with the test-only bind (it used to depend on the unsandboxed fallback).
- `sources/entries/149-mempalace.md`: leading blank line removed; date carries PT (window also in PT and UTC); ChromaDB `/dev/shm` note marked as seen on the author's box only; smoke paths match the code (`~/DEVELOP/pfy-mentat/tmp/mempalace/...`); exact pin and bwrap exit 2 described; cosine/BM25 labelled as observed scores from one run.
- `docs/automation/x-intake-2026-10-29-handoff.md`: test count updated.
- Merged `fix/ci-ubuntu-image` (CI pins ubuntu-24.04 and installs ripgrep) so the tip's CI is green.

## Verify

```
python3 -m unittest tests.test_x_intake_smoke_149          # 18 OK on nimo (bwrap usable)
```

Also run with bwrap hidden, as GitHub's ubuntu-24.04 G0 job does: `PATH=/nonexistent /usr/bin/python3 -m unittest tests.test_x_intake_smoke_149` gives 18 OK, 11 skipped. The first tip CI run (41003563965 at 2c777bd) failed `test_version_pin_is_exact` there because the version probe runs inside bwrap; that test now carries `needs_bwrap`.

Mutation check on nimo (each mutant applied to smoke_149.py, suite run, file restored): all killed.

| Mutant | Result |
|--------|--------|
| drop `--unshare-net` | killed (test_child_has_no_network) |
| `--bind / /` instead of `--ro-bind` | killed (test_child_root_is_read_only) |
| sandbox forced off in `run()` | killed (network and read-only tests) |
| no-bwrap check removed / falls through unsandboxed | killed (test_no_bwrap_exits_2_never_runs_unsandboxed) |
| child HOME = real HOME | killed (test_child_gets_temp_home_with_model_cache) |
| mine_ok check removed | killed (test_mine_failure_fails) |
| `timeout <= 0` guard removed | killed (zero/negative timeout tests check the reason) |
| version pin back to substring | killed (test_version_pin_is_exact) |

CI and pregate results at code SHA 996ea3d: eval-structural 41010561425 success (ubuntu-24.04 G0 and self-hosted nimo G0), operator-launch-filemode 41007276111 success; pregate `996ea3d-20261030T052903Z-459010` OVERALL=PASS pass=6 fail=0 skip=1 (SKIP suite by design). Reviewer verified B1 and B2 fixed at 996ea3d. The commit that fills this line is docs-only.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|--------------|----------|
| Host without bwrap (or userns disabled) | Smoke exits 2 with the bwrap reason; sandbox tests skip | Expected; run on nimo or a host with working bwrap |
| bwrap present but stricter (no /proc) | `bwrap_ok` probe fails, exit 2, never unconfined | Fix the host or the probe; never add a fallback |
| Real MemPalace not staged on nimo | Smoke exits 2 (not staged / model not cached) | Stage `tmp/mempalace/.venv` and warm `tmp/mempalace/home` once |

## Known gaps

- Real MemPalace is still not staged on nimo, so the end-to-end smoke has only run on the Grok Bot box.
- The ChromaDB `/dev/shm` finding is unreproduced on nimo.

## Next step

Reviewer delta gate at the pinned SHA, then bots fast-forward main. No PR (Mark's 2026-10-19 rule).
