# Run log: mvp3-s2s5-1031

Lane: Tester should-fix S2 to S5 on `scripts/pfy_build_local.py`.
Branch: `bot/mvp3-s2s5-1031`. Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp3-s2s5-1031`.
Base: `16f17d8`. Head at start: `a082178` (drop-in only). Remote checked: `origin/main` has no `wall-timeout` or `agent-crashed`.
Launch: 2026-10-31 18:54 PDT (2026-11-01T01:54:01Z). Clock now at plan: 2026-11-01T02:01:38Z.

## Exits (checked before every item)

1. Wall cap: 8 hours from launch (2026-11-01T09:54:01Z) or Sunday 2026-11-01 18:00 PT (2026-11-02T02:00Z), whichever comes first. Leave 20 minutes (stop new items at 2026-11-01T09:34:01Z) to write the handoff.
2. Lane empty: no item left that fits this lane and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores (64) for 5 minutes. Pause 10 minutes, then stop if it persists. At plan: MemAvailable about 57 GiB, load 5.1 on 32 cores.
5. Red base: tests that fail on the base before the change. Record them and skip that area. Do not stop the lane.

Orchestrator stop rules also apply: goal met, no progress, red base after two attempts, host, clock, user stop.

## Plan

Overview: Close Tester should-fixes S2, S3, S4, and S5 in the local build loop. Each item is reproduced red, fixed in `scripts/pfy_build_local.py`, covered by a behavior or fail/recover test, committed, and pushed. The four items share that file, so they run one after another in this worktree. No second worktree and no parallel editor on the same file.

Phases:

- S2 wall budget | `scripts/pfy_build_local.py`, `tests/test_pfy_build_local_review.py` | a run that sleeps past `--wall-timeout` exits 3 with receipt status TIMEOUT and reason wall-timeout, before the retry cap | none | general
- S3 agent crash label | same script, `tests/test_pfy_build_local_review.py` | exit 70 with an empty diff is FAIL reason agent-crashed, and a later fix attempt can still PASS | S2 | general
- S4 receipt label | same script, `tests/test_pfy_build_local_review.py` | a green patch the reviewer rejects has receipt status in PASS, FAIL, BLOCKED, TIMEOUT, ABORTED, reason review-rejected, and the summary line uses that status | S3 | general
- S5 stale worktree | same script, `tests/test_pfy_build_local.py` | SIGKILL leaves the worktree registered; the next run prunes it | S4 | general
- handoff | `docs/ops/HANDOFF-mvp3-s2s5-1031.md`, this log | S table, skips, fail/recover, gate, next step, final state line | S5 | general

Risks:

- A wall default that is too small would turn healthy retries into TIMEOUT. Mitigation: default 7200s, and the new test sets a 2s budget on purpose.
- Relabeling every empty diff as a crash would hide a real no-change. Mitigation: only a non-zero agent exit with an empty diff is agent-crashed. Exit 0 stays no-change.
- Pruning every `local-build-*` worktree would delete a FAIL worktree the runner kept on purpose. Mitigation: prune only the path recorded in the dead pid file.
- Mapping PASS-REJECTED onto FAIL changes a status the mvp3 drop-in named. Mitigation: keep exit 1, keep reason review-rejected, and do not commit. The operator schema status set is the one this lane was told to match.

Pregate: not at start. Runner.Worker is live. Record at the end.
