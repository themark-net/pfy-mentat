# Lane mvp-flake-harness2-1031 (MVP 2026-10-31, wave 8)

Branch: `bot/mvp-flake-harness2-1031`
Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-flake-harness2-1031`
Base: `origin/bot/mvp-integrate-1031`
Run log: `docs/ops/RUN-LOG-mvp-flake-harness2-1031.md` (end with `state: <DONE|lane empty|wall cap> | ...`)
Decisions: `docs/ops/AUTONOMOUS-DECISIONS-mvp-flake-harness2-1031.md`
Handoff: `docs/ops/HANDOFF-mvp-flake-harness2-1031.md`
Needs a local model: no. Do not run scripts/pregate.sh.

## Scope: suite flakes under parallel load
1. `tests.test_harness2_local_stage.StageScriptTests.test_stub_tools_see_state_caches_and_home_stays` failed in the eval-structural step of pregate at 16f17d8 (log: `/home/mark/DEVELOP/pfy-mentat/tmp/pregate-runs/16f17d8-20261101T012942Z-951532/logs/eval-structural.log`, no traceback printed) but passed in ubuntu-parity in the same pregate and alone in 8.7s. Find the cause: timing, shared state, TMPDIR, HOME, or a parallel lane touching a shared path. Reproduce under load (run it 20 times in a loop niced, and with a CPU burner of your own under your tmp/). Fix the test or the code so it is deterministic, with a fail/recover test.
2. Make the structural runner print the traceback of a failing unittest into eval-structural.log (it only printed the test name), with a test.
3. Then loop: run `python3 -m unittest discover -s tests -t .` 3 times niced under the heavy lock with an in-repo TMPDIR and list every test that fails in any run but not all; fix each the same way.

## Added by the operator 19:20 PT (do these first)
A. Root cause seen in CI run 41262832115 (nimo G0 job): the harness2 stage tests failed in tearDown because `~/.cache/uv` changed while they ran (a concurrent pregate on the same host). Make the harness2 stage tests use a private HOME or UV_CACHE_DIR under the test's temp dir, so another process using uv cannot change what they check, and their own uv use cannot touch the real cache. Fail/recover test: change the real-cache stand-in during the test and prove it still passes; prove a write by the test to the real cache path would fail.
B. tests/test_docs_hygiene.py (the shallow-clone branch near lines 68-71): use `self.skipTest("shallow clone: old main SHAs not present")` instead of returning silently. (Only if that file exists on this base; if not, record it as a cross-lane request for bot/backlog-catalog-1030.)
C. scripts/pregate.sh must not run while a G0 job runs on this host: check for a running `Runner.Worker` process (`pgrep -f 'Runner[.]Worker'`) at start and exit with a clear message and a distinct exit code (or wait with a bounded timeout behind a flag). Test it with a fake process name.
Before running any test that uses uv or the full suite, check `pgrep -f 'Runner[.]Worker'`; if a G0 job is running, wait (poll every 60s) until it ends.

## Hard rules (pre-authorized, no questions)

- Follow the orchestrator skill (`~/.grok/skills/orchestrator/SKILL.md`) and the repo skills `prefer-behavior-and-fail-recover-tests`, `repo-handoff-doc-required` and `write-loop-exits-first`. Do not ask questions. Decide conservatively, log each decision as one line in this run's decisions file, and keep going.
- Work only in this worktree. Never touch Mark's main checkout `~/DEVELOP/pfy-mentat`, any other worktree under `tmp/`, or Mark's processes. Never stop or signal a process you did not start.
- Other lanes run in parallel on this host. Stay inside your owned files. If you must change a file another lane owns, do not; record it as a cross-lane request in your handoff.
- No sudo and no system changes. Do not use `/tmp`: scratch goes under this worktree's `tmp/` (gitignored), with `TMPDIR` pointed there.
- Never print, log or commit secret values. Do not read `~/.grok/auth.json`.
- Push only this run's own `bot/` branch, as new commits. No force push, no PR, no merge to main, no tags.
- No em dashes or en dashes in anything you write.
- Every item gets a behavior or fail/recover test when code changes (no tautological unit tests), a commit, and a push. Push after every item.
- Do not end your turn while any process you started is still running. Run long commands in the foreground with bounded waits, or detached with a pid file and a foreground poll loop.

## Shared host: heavy jobs and local models

- Cloud Grok is the default. Never call a local model unless this lane's drop-in explicitly says it needs one.
- Any local-model job (`ollama run`, requests to `127.0.0.1:11434`, `pfy build --local`, local evals) must run under `flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock` and only one local-model job may run on the host at a time. Unload the model when done.
- Targeted tests are fine any time: `nice -n 19 python3 -m unittest tests.test_x`.
- Full `unittest discover`, `make eval-*`, docker builds: run with `nice -n 19` under `flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock`.
- Pregate: at most once, at the end, only if the GitHub runner is idle (`pgrep -f 'Runner[.]Worker'` is empty), under the same flock. Otherwise record "pregate not run: host busy" in the handoff.

## Loop and exits (write these into the run log before any work)

This is a long orchestrator loop, not a single slice. After the listed items, keep taking the next MVP gap that fits this lane until an exit fires.

1. Wall cap: 8 hours from launch, or Sunday 2026-11-01 18:00 PT (PST, 2026-11-02T02:00Z), whichever comes first. Check before every item. Leave 20 minutes to write the handoff.
2. Lane empty: no item left that fits the lane and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped. Record and stop.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail on the base before your change. Record them and skip that area, but do not stop.

Skip items that need special hardware, a human decision (an open OQ), a secret, or Mark's hands. Log each skip with a reason. Do not invent architecture: if an item needs an ADR, write it up as an OQ draft in the handoff and skip it.

## Per item

1. Read the item and its linked docs. Check it is not already done on the base or on `origin/main`.
2. Make the smallest change that closes it, plus behavior or fail/recover tests where code changes.
3. Run the affected test modules (targeted, niced).
4. Commit with a clear message naming the item. Push. Append one line to the run log: `item | commit | tests | result`.

## Finish (on any exit)

Write or update this run's handoff in `docs/ops/`: items done with SHAs, items skipped and why, test evidence, how each change fails and recovers, cross-lane requests, the gate needed (Tester plus Reviewer for runtime changes; pregate plus Reviewer for docs, eval or test-only changes), and the next step. Finish the run log with a final `state:` line. Commit and push. Do not merge.
