# Run log: mvp-localbench-tmpdir-1031

Branch: `bot/mvp-localbench-tmpdir-1031`
Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-localbench-tmpdir-1031`
Base: `origin/bot/mvp-integrate-1031`
Launch: 2026-11-01T01:33:19Z
Wall cap: 2026-11-01T09:33:19Z (8 hours from launch; earlier than Sunday 2026-11-01 18:00 PT / 2026-11-02T02:00Z)
Handoff buffer: stop new items at 2026-11-01T09:13:19Z
Needs a local model: no

Named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files. This card, the drop-in exit list, and `docs/ops/HANDOFF-mvp-localbench-tmpdir-1031.md` are the binding. Decision logged.

```text
LOOP EXIT CARD
Goal (success criteria):     OutdirPathTests.test_relative_outdir_log_path_safe is green with TMPDIR inside the repo and outside the repo. Log paths never resolve outside the outdir and do not depend on where TMPDIR is. Same class of tests/ breakage under an in-repo TMPDIR is fixed. Full unittest discover once under the heavy lock with TMPDIR=$PWD/tmp, count recorded.
1 Goal met:                  targeted unittest green both TMPDIR placements, then full discover count recorded
2 Turn cap:                  8 items (primary fix, sibling TMPDIR fixes, full suite, then next fitting MVP gaps)
3 Budget cap:                cloud Grok only; no local model; no --local; no spend
4 Wall clock:                2026-11-01T09:33:19Z, handoff starts by 2026-11-01T09:13:19Z
5 No-progress:               same failure twice with no new information, or 3 items skipped in a row
6 Human interrupt:           user stop. Do not ask. Conservative reversible choice, one line in the decisions file
7 Error threshold:           3 consecutive same failure, or the drop-in "same failure twice" if it fires first
8 External event:            item already done on base or origin/main; skip that item. Open OQ or ADR need: draft in handoff and skip
Loop type:                   goal
Human gate:                  no merge, no PR. Push this bot/ branch only. Tester plus Reviewer for runtime changes
```

Drop-in exits (checked before every item):

1. Wall cap: 8 hours from launch, or Sunday 2026-11-01 18:00 PT, whichever first. Leave 20 minutes to write the handoff.
2. Lane empty: no item left that fits local-bench outdir path safety and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail on the base before this lane's change. Record them and skip that area. Do not stop the lane.

## Plan

Overview: The local-bench outdir helper emits a relative log path when TMPDIR sits inside the repo, so `test_relative_outdir_log_path_safe` fails on every lane run. Make the safe behavior independent of TMPDIR, cover both placements, sweep `tests/` for the same class of break, then run the full suite once under the heavy lock.

Phases:

- exits-and-plan | docs/ops/RUN-LOG-mvp-localbench-tmpdir-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-localbench-tmpdir-1031.md | exit card on disk before the fix | none | lead
- reproduce-and-fix | local-bench outdir helper, tests/test_local_bench.py | red with TMPDIR=$PWD/tmp, then green inside and outside the repo; behavior test covers both | exits-and-plan | lead
- sibling-tmpdir-tests | tests/ only, plus the helper they call if the helper is the bug | grep gettempdir and /tmp; fix the same class; each fix has a behavior test | reproduce-and-fix | lead
- full-suite | no new product code unless a red test is this lane's bug | nice unittest discover under flock with TMPDIR=$PWD/tmp; count in the run log | sibling-tmpdir-tests | lead
- next-gap | files this lane already owns (local bench path safety) | next MVP gap that fits, or lane empty | full-suite | lead
- handoff | docs/ops/HANDOFF-mvp-localbench-tmpdir-1031.md, this run log | state line, push | always last | lead

Risks:

- Helper vs test: change the helper so a log path never resolves outside the outdir. Do not weaken the assertion to accept a relative escape.
- Parallel lanes: if a fix needs a file another lane owns, record a cross-lane request and skip.
- Full discover is heavy: flock `~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock`, nice -n 19, in-repo TMPDIR. Do not run scripts/pregate.sh.
- Host pressure: sample MemAvailable and load before the suite and before each later item.

Item lines (append after each item): `item | commit | tests | result`

## Progress

state: PLAN | tests: none yet | files: run log and decisions | err: none

Red before the helper change, TMPDIR=$PWD/tmp, `python3 -m unittest tests.test_local_bench.OutdirPathTests`: 3 failures. Inside placement resolved `tmp/lane-tmpdir-inside-.../demo_model.log` to `/tmp/lane-tmpdir-inside-.../demo_model.log`, outside the outdir. The outside placement already stored an absolute path.

Green after the helper change:
- `TMPDIR=$PWD/tmp python3 -m unittest tests.test_local_bench`: Ran 18 tests in 1.341s OK
- `TMPDIR=/dev/shm/pfy-localbench-prove-<pid> python3 -m unittest tests.test_local_bench`: Ran 18 tests in 1.322s OK

Sibling grep: `tempfile.gettempdir()` in tests is a "child HOME is under the process temp dir" check (098, 103, 106, 112). Those follow TMPDIR, so an in-repo TMPDIR does not make them resolve outside an outdir. Hardcoded `/tmp` in `tests/test_pfylib_tmp_cleanup.py` and `tests/support_tmpclean_leaker.py` is the host-leak detector. Not this bug. No second code change.

item | commit | tests | result
log-path-tmpdir | (this commit) | TMPDIR=$PWD/tmp and TMPDIR=/dev/shm/... unittest tests.test_local_bench | 18 OK both ways
