# Run log — orch-decisions-1009

**Slug:** orch-decisions-1009  
**Date:** 2026-10-09  
**Branch:** `build/orch-decisions-1009` @ `8c0b547` (same as `origin/main`)  
**Worktree:** `/home/mark/DEVELOP/pfy-mentat/tmp/orch-decisions-1009`  
**Decisions:** [AUTONOMOUS-DECISIONS-2026-10-09.md](AUTONOMOUS-DECISIONS-2026-10-09.md)  
**Request:** decide-and-ship batch. Pre-authorized. Not a Feature GO.

Remote check before code: `git fetch --all` from this worktree. `HEAD` equals `origin/main` (`8c0b547`). `origin/catalog/x-intake-098-100` and `origin/catalog/agent-substrate-102` are ancestors of that commit. No remote branch already contains the HOME isolation, TimeoutExpired receipt, full harness pin, unscored bench stage, TODO dedupe, or the skill cross-links this run adds.

## Overview

Nine pre-authorized nits land on `build/orch-decisions-1009`. Items that share a file are one workstream. Independent workstreams run in separate worktrees under `/home/mark/DEVELOP/pfy-mentat/tmp/` and merge back only after their definition of done is green. The lead owns the run log, the decisions file, the final handoff, the push of this branch only, and the PR body. Catalog HOLD 070–075, eval-harness, and issue #76 stay untouched. The founder checkout `/home/mark/DEVELOP/pfy-mentat` stays untouched.

## Phases

- xintake-nits | `examples/x-intake-local/smoke_098_100.py`, `examples/x-intake-local/README.md`, `sources/entries/100-repository-harness.md`, `docs/automation/x-intake-2026-10-07-handoff.md`, `.gitignore`, new `tests/test_x_intake_smoke_098_100.py` | HOME isolation for sponsio and repoharness; TimeoutExpired on opensteps `hook()` and repoharness `hj()` becomes exit 1 with a timeout reason; full harness sha256 pinned and mismatch exits 2 before exec; three smoke receipt dirs ignored while `pipelines/smoke/kolibri1/latest.json` stays tracked. Tests fail on the old code, then pass. `git status --porcelain pipelines/smoke` empty after a smoke run. | none | general
- substrate-commands | `docs/automation/agent-substrate-2026-10-08-handoff.md` | The Stage A command block contains `mkdir b && ./runsc spec -bundle b -- <cmd>` and the root.path=/ read-only + terminal=false note before run, checkpoint, and restore. `python3 scripts/catalog_check.py` and `make eval-structural` green. Docs only. Do not run runsc. | none | general
- atg-stage | `examples/atg-compile/bench.py`, `tests/test_atg_compile_bench.py` | `--integration-stage` has no default. Absent writes `unscored` (field kept) on the cannot-run JSON and the scored receipt. A passed value is copied. Committed receipts are not rewritten. A test that runs without a live model fails on the old `I1` constant and passes after. No Ollama, no llama-server. | none | general
- docs-todo-skills | `docs/TODO.md`, `bootstrap/grok-cli/skills/one-shot/SKILL.md`, `bootstrap/grok-cli/skills/agent-loops/SKILL.md`, `bootstrap/grok-cli/skills/prefer-behavior-and-fail-recover-tests/SKILL.md`, `docs/ops/multi-cli-parity.md` | GitHub-issues table has one row each for T-0075 and T-0007, status done. File starts at `# TODO`. Skill cross-links resolve to the existing mattpocock `to-spec` and `tdd` SKILL.md paths. Claude Code parity section cites existing repo paths. `make smoke-grok-skills` and `make eval-structural` green. T-0076 and T-0040 marked done. Do not close GitHub issues. | none | general
- handoff | `docs/ops/HANDOFF-orch-decisions-1009-2026-10-09.md`, `docs/ops/PR-BODY-orch-decisions-1009.md`, `docs/PENDING-HANDOFF.md`, `docs/TODO.md` only if a phase left a status line | What landed, decisions count, baseline vs final test lines, BLOCKED items, branch, head SHA, push result, compare URL. Push only `build/orch-decisions-1009`. Do not merge. | xintake-nits, substrate-commands, atg-stage, docs-todo-skills | lead

## Risks

- Shared `smoke_098_100.py` across items 1–3: one workstream, one worktree, so the agents cannot overwrite each other.
- Repoharness hash check would block the HOME and timeout stubs: `HARNESS_SHA256` overrides the expected digest; unset keeps the release pin. Logged.
- atg scored e2e skips unless `ATG_REPO` is a clean pin checkout with `.venv`. The host checkout is `9393767`, not pin `543e778`. A detached worktree plus a `.venv` symlink is allowed; do not move that repo's branch. The cannot-run JSON assertion runs with no model either way.
- `docs/TODO.md` is one workstream (items 7–9) so the status edits do not collide.
- Baseline suite is running on the lead worktree while phase worktrees edit copies. Final numbers are re-run on the merged tree.
- `gh` is not logged in. PR body goes to the docs path and `/tmp/pr-orch-decisions-1009.md`. Do not try to log in.

## Exits

| Exit | When |
| --- | --- |
| Goal met | Every phase is DONE, BLOCKED, or SKIPPED, and the handoff is written |
| No progress | The same failure twice on one phase |
| Red base | Tests were already red and two attempts did not fix the failure we walked into |
| Host | Machine out of memory or swap-full. Stop loading things |
| Clock | About 6 hours from 2026-10-09 run start. Re-invoke resumes from this log |
| User | The user tells us to stop |

## Baseline

Command (lead worktree, before phase merges): `python3 -m unittest discover -s tests -t .` ; `make eval-structural` ; `python3 scripts/catalog_check.py`.  
Log: `/tmp/orch-decisions-1009/baseline.txt`  
Result (lead tree at `8c0b547`, before phase merges):

- `python3 -m unittest discover -s tests -t .` → Ran 184 tests in 3.172s · OK (skipped=4) · exit 0
- `make eval-structural` → STRUCTURAL EVAL: PASS · exit 0 (inner pfylib unittest Ran 184 tests in 3.092s · OK skipped=4)
- `python3 scripts/catalog_check.py` → PASS catalog-check slim-subset ok n_json=7 · exit 0

## Phase results

Spawned 2026-10-09 after this plan was on disk. Worktrees are local branches off `8c0b547`. Not pushed.

- xintake-nits | DONE | tests: red `FAILED (failures=5)` then `Ran 5 tests in 0.672s OK`; catalog_check PASS n_json=7; gitignore porcelain empty | files: 6 | err: none | commit e22878f merged as a1261ed
- substrate-commands | DONE | tests: order ok; catalog_check PASS n_json=7; STRUCTURAL EVAL: PASS | files: 1 | err: none | commit afc6f58 (fast-forward onto the lead branch)
- atg-stage | DONE | tests: red `AssertionError: 'I1' != 'unscored'` then `OK (skipped=2)` without ATG_REPO; lead re-ran fake-server e2e with the pin worktree `OK` | files: 2 | err: none | commit c63f746 merged as c171f45
- docs-todo-skills | DONE | tests: todo uniq ok; skill links ok; claude parity citations ok; smoke-grok-skills PASS; STRUCTURAL EVAL: PASS | files: 5 | err: none | commit 7fec982 merged as e23c325
- project-map | DONE | `.project-map/index.html` refreshed after the merges | err: none
- handoff | DONE | this log, HANDOFF, PENDING-HANDOFF section, PR body | err: none

state: DONE | tests: final unittest Ran 190 tests in 3.882s OK (skipped=4); eval PASS; catalog n_json=7; smoke-grok-skills PASS | files: four phase merges plus handoff docs | err: none

## Push

Recorded in the orchestrator final message after `git push -u origin build/orch-decisions-1009`. Not force. Not main.
