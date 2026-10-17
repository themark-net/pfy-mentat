/orchestrate — follow ~/.grok/skills/orchestrator/SKILL.md.

This request is PRE-AUTHORIZED by the owner. Ask no questions.

> Drop-in written 2026-10-17. Follow-ups to the X-intake smoke line (#284 isolation, #285-#287 entries 103-111, #289 orch-fixes-1011 receipts/timeouts/cleanup). Checked against origin/main 0d574f0. Some items are partly in place on main (noted per item): verify first, then close only the gap. Chained after the orch-fixes-1011 recheck run; if that run's branch build/orch-fixes-1011-recheck pushed a code fix to a file you touch, `git fetch origin` and read its diff first so you do not undo it (do not merge or rebase onto it; your base stays origin/main).

## Context
- Worktree (your only working tree): /home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups
- Branch: build/pr284-followups (from origin/main 0d574f0649ccfe5bdd5d5384786c74173fb6e41e). First commit already on it: this drop-in at docs/build-dropins/pr284-followups.md.
- Run log (update after every item): docs/ops/RUN-LOG-pr284-followups.md. If it already exists, RESUME from it.
- Decisions: docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-pr284-followups.md (create; one line per decision).
- Handoff (write at every exit): docs/ops/HANDOFF-pr284-followups-2026-10-17.md. Must name the final head SHA, branch, baseline vs final test counts, per-item status (DONE with commit SHA / ALREADY-DONE with evidence / SKIPPED or BLOCKED with reason), mutation-check notes, local CI results, decisions, and the exit that fired.
- Smoke code: examples/x-intake-local/smoke.py (shared helpers `pinned`, `timeout_reason`, `PAID_KEYS`, `write`, `PFY_SMOKE_RECEIPT_DIR`) and smoke_098_100.py ... smoke_122_124.py; tests in tests/test_x_intake_smoke_*.py.

## Hard rules (owner-approved unattended run; ask no questions)
- Your only working tree is /home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups (above). Never touch the founder checkout /home/mark/DEVELOP/pfy-mentat: no edits, stash, reset, pull, checkout or index changes there. Never touch other worktrees under tmp/.
- No sudo, no package installs, no system/host/service changes, no model loads, no spending, no sign-ins, no posting anywhere. gh is not logged in: do not try. Write nothing outside ~/DEVELOP except /tmp.
- Never print, log or commit secrets or auth tokens. If a value might be secret, mask it (first 4 chars + `***`).
- Never pause, stop or kill any process you did not start (Mark's grok sessions and the Leasegrid test cycle run alongside you). Keep the host light: no parallel full-suite runs, no heavy benches.
- Do not touch draft PRs #255 or #258 or their branches. Catalog HOLD / parked items stay untouched.
- Open NO pull request. Push ONLY your branch: `git push -u origin build/pr284-followups` (SSH origin). Never merge, deploy, force-push, or push any other branch.
- Small reversible ambiguities: decide conservatively yourself and append one line per decision to docs/ops/AUTONOMOUS-DECISIONS-2026-10-17-pr284-followups.md (format: choice | alternatives | why).

## Exits (written before the loop; check them before every item and every retry)
1. STOP file: if `/home/mark/DEVELOP/pfy-mentat/tmp/pr284-followups/tmp/STOP` exists, stop now (status STOPPED_EXIT: stop-file).
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

## Items (in order; DoD in brackets)
1. Receipt SHA source + override WARN. `pinned()` already records `expected[var] = {value, source, pin}` and WARNs on any env value. Make sure HARNESS_SHA256, GRAPHJIN_SHA256 and CM_SHA256 receipts carry the expected SHA and its source (pin/env), WARN on stderr only when the override differs from the pin (compare case-insensitively for sha vars), and print no WARN when the override equals the pin. [behavior tests run the real smokes (stub binaries) for pin, env-different (WARN + source env) and env-equal-to-pin (no WARN) for each of the three vars; mutation: drop the equality check → env-equal test goes red]
2. Timeout text + sponsio timeout test. Every smoke records timeouts only via `timeout_reason(tag)` (check all smoke*.py, including 112-124, e.g. smoke_112_114.py `daemon_stop: "timeout"` and any hand-written "timed out" text), and docs/README describe the same text. A sponsio timeout test exists (tests/test_x_intake_smoke_098_100.py test_b_sponsio_timeout_reason_is_exact); confirm it drives a real timeout through PFY_XINTAKE_TIMEOUT and fails if the text changes; strengthen only if not. [grep shows no other timeout reason text; sponsio test green, red under mutation]
3. Stage A doc commands. docs/automation/agent-substrate-2026-10-08-handoff.md (Stage A block): every spec edit is a copy-paste command that actually runs. [extract each block, run it against a temp copy of the spec under /tmp, assert the resulting JSON; fix any command that fails or depends on cwd]
4. Handoff notes. docs/automation/x-intake-2026-10-11-handoff.md (entries 109-111) says "190 tests"; that count is wrong for its slice. Recompute it: in a throwaway `git worktree add /tmp/pfy-109-111 a5c0362` run `python3 -m unittest discover -s tests -t .`, record the true count and result, remove that worktree, and fix the sentence (also check the 2026-10-10 handoff's 190 the same way at fb3beb5 and fix only if wrong). [handoff numbers match a recorded rerun; decision line logged]
5. Gitignore smoke receipts for 103-111. Ensure pipelines/smoke/ receipt dirs for entries 103-111 (bugpatrol, graphjin, antislop, rulora, har, cassmemory, smolvm, brigade, runx, plus any other dir those smokes actually write) are ignored, without ignoring pipelines/smoke/ broadly (kolibri1/latest.json stays tracked). [a test runs each 103-111 smoke into the real pipelines/smoke path (stub/skip path is fine) and asserts `git status --porcelain pipelines/smoke` is empty and kolibri1/latest.json is still tracked]
6. graphjin log handle. smoke_103_105.py graphjin_world: the serve.log handle is closed on every path (Popen raises, server never comes up, normal run), and the log tail in the receipt is read after flush. [tests make Popen raise and make the server exit early; assert the handle is closed (no ResourceWarning under `-W error::ResourceWarning`) and the receipt carries the log tail]
7. smoke_106_108 enforces work_dir and XDG. The har smoke must FAIL (non-zero, reason names it) when work_dir_under_temp_home is false, and every child gets XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_DATA_HOME and npm_config_cache under the temp HOME (check all children, including cass-memory and rulora runs, not only har). [behavior tests: a stub child dumps its env and cwd; assert the paths are under the temp HOME; a forced outside work dir yields FAIL]
8. Tests clean up /tmp pfylib-*. tests/test_pfylib_tmp_cleanup.py exists; extend coverage so no test module (including the x-intake smoke tests and launcher tests added since #289) leaves new /tmp/pfylib-* (or the smoke tests' own /tmp prefixes) behind. [before/after diff around a full suite run is empty; record the diff in the run log]
9. smoke_098_100 uses the shared PAID_KEYS. It imports from smoke but not PAID_KEYS; replace any local key list/scrub with `smoke.PAID_KEYS`. [test sets a dummy value (e.g. `OPENAI_API_KEY=pfy-test-dummy`) for every PAID_KEYS name and asserts none reach the sponsio/opensteps/repoharness child env; never use real keys]
10. node --version through a stripped env. smoke_103_105.py:120 and smoke_106_108.py:90 run `node --version` with the full host env; run it through the same stripped/clean env the smokes use for children (no PAID_KEYS, temp HOME). [stub node dumps its env; tests assert no PAID_KEYS and HOME is the temp HOME for both smokes; mutation: pass os.environ → red]
11. test_x_intake_smoke_109_111: (a) use a temp receipt dir via PFY_SMOKE_RECEIPT_DIR instead of writing pipelines/smoke/* in the repo (the brigade timeout test currently reads ROOT/pipelines/smoke/brigade/latest.json); (b) add a test that forces the no-bwrap path (bwrap absent from PATH) and asserts the documented fallback/FAIL; (c) add an `--unshare-pid` test asserting the flag is passed (and its documented behavior when unsupported). [tests green; repo pipelines/smoke unchanged after the module runs]
12. smolvm alpine digest. smoke_109_111.py runs `machine run --image alpine` (pulls from Docker Hub). Make the smolvm receipt record the resolved alpine image digest (and the image ref, honoring $SMOLVM_IMAGE), with a test using a stub smolvm. Then the first nimo run: ONLY if `~/DEVELOP/pfy-mentat/tmp/smolvm/smolvm` already exists and /dev/kvm is read/write for this user, run `python3 examples/x-intake-local/smoke_109_111.py --entry smolvm` once, and record the digest in sources/entries/109-smolvm.md and the 2026-10-11 handoff (commit the receipt with `git add -f` only if it holds no secrets). Do not download or install smolvm. If it is absent (it was absent on 2026-10-17), mark the live part BLOCKED (smolvm not installed on nimo) in the handoff and keep the code+test part. [receipt field + test; live digest recorded or BLOCKED noted]

## Outcome
- One commit per item on build/pr284-followups; push it (`git push -u origin build/pr284-followups`) after each item or at least at every exit. Open NO PR and write no PR body; leave the compare URL https://github.com/themark-net/pfy-mentat/compare/main...build/pr284-followups in the handoff.
