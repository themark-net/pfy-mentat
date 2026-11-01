# Run log mvp-cloud347-1031

Lane: wave 9 cloud fixes. Branch `bot/mvp-cloud347-1031`. Worktree `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-cloud347-1031`. Base `origin/bot/mvp-probe-int-1031` (this branch is that tip plus the drop-in `79cd260`).

Launch: 2026-11-01T02:34:05Z.
Wall cap: 8 hours from launch, so 2026-11-01T10:34:05Z, or Sunday 2026-11-01 18:00 PT (2026-11-02T02:00Z), whichever comes first. The 8 hour cap binds first. Leave 20 minutes to write the handoff. No new item after 2026-11-01T10:14:05Z.
Clock check before every item. Host at launch: MemAvailable about 54 GiB (56957692 KiB), 32 cores, load about 3.45. Pressure line is 16 GiB or load over 64 for 5 minutes. `Runner.Worker` pid 1511538 was alive, so no uv, no `./pfy`, and no python test suite until that process is gone. Pregate is not this lane's job.

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     Pass3 findings 3, 4, and 7 are closed on scripts/pfy_build_cloud.py with a behavior or fail/recover test each. A patch that only removes `rm -rf /` can land. `.env.bak`, `.env.local`, and other `.env.*` names except `.env.example` are protected. `reap` exits non-zero with a clear reason when the ABORTED receipt cannot be written, and a later reap can still write it. Further probe-int cloud gaps that need no ADR are fixed or recorded as skips.
1 Goal met:                  nice -n 19 python3 -m unittest tests.test_pfy_build_cloud is OK after each code item, and the new assertion fails if that finding regresses.
2 Turn cap:                  the phases below, then the handoff. The agent-loops default of 8 is not the cap. The drop-in says keep taking the next fitting gap until an exit fires.
3 Budget cap:                Cloud Grok only. No local model. No --local. Fake grok for tests. No spend.
4 Wall clock:                2026-11-01T10:34:05Z, or 2026-11-02T02:00Z, whichever first. Handoff starts 20 minutes earlier (2026-11-01T10:14:05Z).
5 No-progress:               the same failure twice with no new information, or 3 items skipped in a row.
6 Human interrupt:           user says stop. Do not ask questions. Do not merge to main. Push of this bot/ branch is pre-authorized.
7 Error threshold:           3 consecutive same failures, then stop. A red base test is recorded and that area is skipped. It does not by itself stop the lane.
8 External event:            stop a line if origin/main or this base already closed it. git fetch before every item.
Loop type:                   goal
Human gate:                  no merge, no PR, no tag. Tester plus Reviewer at handoff for runtime changes.
```

Orchestrator clock of about 6 hours does not apply. This drop-in sets the 8 hour cap.

Named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. This card, the drop-in exit list, and `docs/ops/HANDOFF-mvp-cloud347-1031.md` are the binding.

## Exits (drop-in, written before code)

1. Wall cap: the clock above. On this exit, write the handoff and stop.
2. Lane empty: no item left that fits this lane and the drop-in rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped. Record and stop.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores (64) for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail on the base before this lane's change. Record them and skip that area. Do not stop the lane.

Skip items that need special hardware, a human decision (an open OQ), a secret, or Mark's hands. Log each skip with a reason. An item that needs an ADR is an OQ draft in the handoff, then a skip. Do not invent architecture.

## Plan

Overview: Pass3 review findings 3, 4, and 7 are still present on this base (`diff_aims_at_root` scans the whole diff, `_protected` misses `.env.*` except the exact `.env` name, and `reap` returns 0 after a failed ABORTED write). Dogfood5 skipped those three because this file belonged to probe-int. This lane closes them in order, then takes any remaining probe-int cloud gap that does not need an ADR. The same-process symlink sandbox in that handoff needs an ADR, so it stays a skip.

Phases:

- loop-card | `docs/ops/RUN-LOG-mvp-cloud347-1031.md`, `docs/ops/AUTONOMOUS-DECISIONS-mvp-cloud347-1031.md` | exits and phases are in this file before any product edit | depends on nothing | general
- scan | read-only | findings 3, 4, and 7 are open here and absent from `origin/main` (that file has no `diff_aims_at_root`) | loop-card | general
- root-added-only | `scripts/pfy_build_cloud.py`, `tests/test_pfy_build_cloud.py` | deleting `danger.sh` whose only line is `rm -rf /` can PASS and land `kept.py`; an added `rm -rf /` and an added `rm -rf /tmp/x` stay `review-rejected` with no branch | scan | general
- env-variants | same two files | `.env.bak` and `nested/.env.local` are `protected-path-changed`, the secret text is absent from the receipt, and a retry that writes `.env.example` plus `kept.py` can PASS | root-added-only | general
- reap-receipt | same two files | when the ABORTED receipt cannot be written, `--reap` exits 1, stderr names the receipt path, and the pid file remains; a second `--reap` after the path is a directory writes `ABORTED` and exits 0 | env-variants | general
- rescan | probe-int handoff, fetched remotes | each remaining no-ADR cloud gap is fixed, or the skip reason is in the handoff | reap-receipt | general
- handoff | `docs/ops/HANDOFF-mvp-cloud347-1031.md`, final `state:` line | committed and pushed, no merge | rescan | general

One workstream. Every code phase edits the same runner and its test module, so they run in order. The lead implements them. No second editor.

Risks:

- `Runner.Worker` shares `~/.cache/uv`. Mitigation: while `pgrep -f 'Runner[.]Worker'` matches, do not run uv, `./pfy`, or any python test suite. Poll every 60s. Do not run `scripts/pregate.sh`.
- Parallel lanes own other files. Mitigation: edit only the two code files and this lane's three docs. A needed edit elsewhere is a cross-lane request.
- Treating `.env.example` as secret would block a normal sample file. Mitigation: the env test lands `.env.example` on the retry.
- Unlinking the pid file after a failed receipt write would make a second `--reap` a no-op. Mitigation: keep the pid file until the ABORTED receipt is written.
- A real grok call could spend or read auth. Mitigation: tests use a fake `--grok-cmd`. No `--local`.

## Item log

Format: `item | commit | tests | result`

- loop-card | 34d7992 | docs only | PASS
- root-added-only | pending | tests.test_pfy_build_cloud | red before the fix: test_removing_a_root_delete_can_land returned 1, reason review-rejected. test_added_tmp_delete_stays_rejected passed on that tree. After the fix the module is OK (69 tests).

Scan at 2026-11-01T02:34Z, before code: `diff_aims_at_root` still searches the whole diff. `DEFAULT_PROTECT` lists `.env` and `_protected` does not special-case `.env.*`. `reap` uses `except OSError: pass` and then `return EXIT_OK`. `origin/main` at `c0d38af` has no `diff_aims_at_root`. Probe-int handoff's remaining cloud gap is the same-process symlink write, which that handoff already marks as an ADR.
