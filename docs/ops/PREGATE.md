# Pregate (local, free)

Run this **before** any Tester or Reviewer gate request. Attach the summary file. It catches the failure classes that burned ~49% of weekly Grok Bot usage on gate rounds (unsandboxed tests, red ubuntu CI, test-runner cheats, orphan processes).

## Rule

1. Run pregate on the branch tip (or the SHA you will gate).
2. Attach `tmp/pregate-summary.md` (or the copy under the nested run dir) to the gate request.
3. Do **not** spend Tester/Reviewer turns until overall is **PASS**, or until you have an explicit waiver for a documented known gap.

## How to run (nimo)

From any pfy-mentat worktree that has this script (usually a bot branch worktree under `~/DEVELOP/pfy-mentat/tmp/…`):

```bash
# Clean isolated worktree at REF (default HEAD). Preferred.
./scripts/pregate.sh
./scripts/pregate.sh origin/main
./scripts/pregate.sh 997d892

# Already on the SHA and tree is clean:
./scripts/pregate.sh --in-place

# Dirty tree (dev only):
./scripts/pregate.sh --in-place --allow-dirty

# Keep the nested worktree for debugging:
./scripts/pregate.sh --keep-worktree REF

# One check only (lint|eval-structural|suite|ci-parity|orphans|gate-hash):
./scripts/pregate.sh --only ci-parity 2fadea1

# Quick pre-check in seconds (not for gate attachment); the long discover lives in eval-structural:
for c in lint ci-parity gate-hash; do ./scripts/pregate.sh --only $c REF; done

# Re-run unittest even though eval-structural already did:
./scripts/pregate.sh --force-suite REF
```

Constraints (same as other nimo bot work):

- Temps under the worktree `tmp/` or `~/DEVELOP/pfy-mentat/tmp/` — never `/tmp` for project scratch.
- Never touch Mark’s dirty `~/DEVELOP/pfy-mentat` main checkout or other live worktrees.
- No sudo, no system package changes.
- Do not print or commit secrets; do not read `~/.grok/auth.json`.

## Output

- **Summary:** `<run-root>/tmp/pregate-summary.md` and a pointer at `<invoking-repo>/tmp/pregate-latest-summary.md`
- **Logs:** `<run-root>/tmp/pregate-logs/*.log`
- **Exit:** `0` on overall PASS, `1` on any FAIL, `2` on usage/setup errors

Nested runs land under `~/DEVELOP/pfy-mentat/tmp/pg/<shortsha>-<stamp>/` (short product tmp/pg/ so bwrap sockets fit sun_path) and are removed on exit unless `--keep-worktree`.

## Checks

| check | what it covers |
|---|---|
| **lint** | CI lint surface (this repo has no ruff job): launcher `100755`, `./pfy help`, `check_no_encoded_payloads`, `smoke_contract_lint`, `catalog_check`, `py_compile` of board/gui |
| **eval-structural** | `.github/workflows/eval-structural.yml` G0 ubuntu steps, including the full `unittest discover` that `run_structural.py` runs (pfylib_unittests): structural + golden, gab/jev/launch-wizard selftests, toolset matrix/plan, hedge decide, launcher exec, encoded-payload scan |
| **suite** | Standalone `python3 -m unittest discover -s tests -t .`. It is SKIPPED by default because eval-structural's `run_structural.py` already runs the same discover, sandbox tests included (916 tests on 997d892). Use `--force-suite` to run it again, or `--only suite` on its own. |
| **ci-parity** | Curated PATH **without bwrap**; `PFY_STATE_DIR` like the ubuntu job; static + behavioral pin that runtime-dir tests pass `auto_unsafe=False` (catches the 2fadea1 ubuntu failure where those tests auto-added `--unsafe-no-sandbox`) |
| **orphans** | Live processes whose argv references this run's root or scratch dir, plus `orphan*.pid` / heartbeat files there. Other worktrees' runs are ignored and never signalled. |
| **gate-hash** | `tests/` and gate basenames (`conftest.py`, `sitecustomize.py`, `pytest.ini`, …) match git HEAD; no untracked gate/test cheats |

Past failure types from `GATE-NOTES-fix2.md` / `HANDOFF-pfy-local-build-mvp.md` mapped in:

- Unsandboxed / `--unsafe-no-sandbox` auto-add → **ci-parity**
- Red ubuntu CI / bwrap missing → **ci-parity** + **eval-structural** (full discover, with sandbox tests on a host with bwrap)
- Test-runner cheats (new conftest/sitecustomize, untracked tests) → **gate-hash**
- Orphan processes after SIGTERM / hang scenarios → **orphans**
- Structural G0 drift → **eval-structural** + **lint**

## What pregate does not replace

- Live model eval (`./pfy eval-local-build`)
- Tester/Reviewer judgment on product gaps called out as known
- Merging or pushing to `main`

## See also

- [HANDOFF-pregate.md](HANDOFF-pregate.md)
- [GATE-NOTES-fix2.md](GATE-NOTES-fix2.md)
- [HANDOFF-pfy-local-build-mvp.md](HANDOFF-pfy-local-build-mvp.md)
