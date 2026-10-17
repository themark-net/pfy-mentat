/orchestrate — follow ~/.grok/skills/orchestrator/SKILL.md.

This request is PRE-AUTHORIZED by the owner. Ask no questions.

> Drop-in revised 2026-10-17 (rerun of the 2026-10-11 orch-fixes-1011 prompt). Staleness check against origin/main 0d574f0: all 8 backlog items below were implemented on build/orch-fixes-1011 and squash-merged to main as #289 (7702826, 2026-10-12); main has since moved through #290-#299 (launcher phase 1, X intake 112-124, smoke #298 follow-ups). The old worktree tmp/orch-fixes-1011, branch build/orch-fixes-1011, and base 27c2d3b are retired; do not reuse them. This run is therefore a **verify-and-repair** pass: confirm each item's DoD still holds on current main, and fix only real regressions. Refinements of these same areas are queued for the follow-up run `docs/build-dropins/pr284-followups.md` (it starts after this run exits); do not do that list's work here.

## Context
- Worktree (your only working tree): /home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011-recheck
- Branch: build/orch-fixes-1011-recheck (from origin/main 0d574f0649ccfe5bdd5d5384786c74173fb6e41e). First commit already on it: this drop-in at docs/build-dropins/orch-fixes-1011.md.
- Run log (update after every item): docs/ops/RUN-LOG-orch-fixes-1011-recheck.md. If it already exists, RESUME from it.
- Decisions: docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-orch-fixes-1011-recheck.md (create; one line per decision).
- Handoff (write at every exit): docs/ops/HANDOFF-orch-fixes-1011-recheck-2026-10-17.md. Must name the final head SHA, branch, baseline vs final test counts, per-item status (ALREADY-DONE with evidence / DONE with commit / SKIPPED with reason), local CI results, decisions, and the exit that fired.

## Hard rules (owner-approved unattended run; ask no questions)
- Your only working tree is /home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011-recheck (above). Never touch the founder checkout /home/mark/DEVELOP/pfy-mentat: no edits, stash, reset, pull, checkout or index changes there. Never touch other worktrees under tmp/.
- No sudo, no package installs, no system/host/service changes, no model loads, no spending, no sign-ins, no posting anywhere. gh is not logged in: do not try. Write nothing outside ~/DEVELOP except /tmp.
- Never print, log or commit secrets or auth tokens. If a value might be secret, mask it (first 4 chars + `***`).
- Never pause, stop or kill any process you did not start (Mark's grok sessions and the Leasegrid test cycle run alongside you). Keep the host light: no parallel full-suite runs, no heavy benches.
- Do not touch draft PRs #255 or #258 or their branches. Catalog HOLD / parked items stay untouched.
- Open NO pull request. Push ONLY your branch: `git push -u origin build/orch-fixes-1011-recheck` (SSH origin). Never merge, deploy, force-push, or push any other branch.
- Small reversible ambiguities: decide conservatively yourself and append one line per decision to docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-orch-fixes-1011-recheck.md (format: choice | alternatives | why).

## Exits (written before the loop; check them before every item and every retry)
1. STOP file: if `/home/mark/DEVELOP/pfy-mentat/tmp/orch-fixes-1011-recheck/tmp/STOP` exists, stop now (status STOPPED_EXIT: stop-file).
2. Tries: at most 3 attempts per item. After the 3rd failed attempt, mark the item SKIPPED with the reason and move on.
3. Skips: stop after 3 SKIPPED items in a row (STOPPED_EXIT: 3-skips). An item verified as already met on origin/main is ALREADY-DONE, not SKIPPED.
4. Wall clock: note the start time from `date` in the run log. Start no new item after 5h30m; stop by about 6h (STOPPED_EXIT: time-cap). A backstop `timeout` kills the process at 6h15m, so commit as you go.
5. No progress: 3 identical failures (same error or same diff) on one item = SKIPPED immediately.
6. Red base: if the baseline suite is broken beyond the known box-only test_hedge test_detector_runs_offline, record it and stop (BLOCKED: red-base).
7. Goal met: every item DONE, ALREADY-DONE or SKIPPED, final checks recorded (DONE).
On every exit: update the run log and the handoff doc, commit, and push the branch.

## Testing rules
- Before any change, record the baseline full suite (`python3 -m unittest discover -s tests -t .`) count and result in the run log.
- Behavior-level tests only (drive the real smoke/CLI/subprocess and assert receipts, stderr, exit codes, files). No tautological unit tests.
- For each fix, show the new test failing without the fix (revert the fix, run, note the failure in the run log), then passing with it. Where it makes sense, do a quick mutation check (break the line the test guards, confirm the test goes red, restore) and note it.
- Local CI before the final push: run every `run:` step of .github/workflows/eval-structural.yml locally (structural + golden evals, the gab/jev/launch-wizard selftests, the full unittest suite), plus `python3 scripts/catalog_check.py` and `python3 scripts/check_no_encoded_payloads.py`. Do not commit regenerated pipelines/eval/*.latest.md unless they already change on main runs; restore them with `git checkout --` otherwise. Record results in the run log and handoff; a failure identical on the baseline is not a regression, note it.

## Commits
- Exactly one commit per item that changes something (code + its test + any doc for that item together), message `<area>: <item n> <short what>`. An ALREADY-DONE item gets no code commit; record its evidence (file:line on origin/main, test name) in the run log.
- Run log and handoff updates may be their own `docs:` commits.

## Backlog (verify each DoD on current main; repair only if it no longer holds)
Note: entries 109-124 smokes were added after the original prompt. Where a DoD says "every smoke" or lists receipt dirs, check the current set of examples/x-intake-local/smoke*.py and pipelines/smoke/ dirs, not only 098-108.
1. Smoke receipts record the expected sha and its source (pin vs env) and print a stderr WARN line when HARNESS_SHA256, GRAPHJIN_SHA256 or CM_SHA256 overrides the pinned value. [receipt JSON contains expected sha + source field; env override emits WARN on stderr; a test covers pin and env cases] (merged: smoke.py `pinned()`; the "no WARN when override equals the pin" refinement belongs to the follow-up run, not here)
2. Consistent timeout message text across all smokes, plus a sponsio timeout test. [one shared timeout message format (`timeout_reason`) used by every smoke; a test drives a sponsio timeout and asserts the message] (merged; check whether later smokes, e.g. smoke_112_114.py, bypass `timeout_reason` and report it; fix only if a smoke writes a timeout `reason` without it)
3. Stage A doc (Agent Substrate) lists its spec edits as copy-paste commands. [doc contains runnable copy-paste command blocks for each spec edit; run each block against a temp copy to prove it works]
4. x-intake handoff docs mention `git add -f` for receipts; the 2026-10-09 handoff notes the temp atg worktree was removed. [both doc edits present]
5. .gitignore the pipelines/smoke receipt dirs for entries 103-108 (rulora, har, cassmemory, bugpatrol, graphjin, antislop) so `git status --porcelain pipelines/smoke` stays empty after running smokes. [`git check-ignore` passes for each receipt path; pipelines/smoke/kolibri1/latest.json stays tracked]
6. graphjin_world: close the server log file handle if Popen raises. [a test makes Popen raise and asserts the handle is closed]
7. smoke_106_108.py: FAIL if work_dir_under_temp_home is false; XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_DATA_HOME and npm_config_cache point under the temp HOME; ~/.har/otel-hooks is checked inside the temp HOME. [tests cover the FAIL path and the env vars]
8. Test suite cleans up the /tmp/pfylib-* dirs it creates. [no new /tmp/pfylib-* left after a full test run]

## Outcome
- Commit on build/orch-fixes-1011-recheck only; push it (`git push -u origin build/orch-fixes-1011-recheck`). Open NO PR and write no PR body; just leave the compare URL https://github.com/themark-net/pfy-mentat/compare/main...build/orch-fixes-1011-recheck in the handoff.
- If every item is ALREADY-DONE, that is a valid DONE outcome: the branch then carries the drop-in, run log, decisions and handoff only.
