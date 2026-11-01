# RUN-LOG mvp-backlog-fu-1031

START: 2026-11-01 01:54 UTC (2026-10-31 18:54 PT, still PDT). Launch commit `1ed4007`.
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-backlog-fu-1031`
Branch: `bot/mvp-backlog-fu-1031` (even with `origin/bot/mvp-backlog-fu-1031` at `1ed4007`).
Base: `origin/bot/backlog-catalog-1030` at `2a74482`. `origin/main` is `c0d38af` (this branch is 21 commits ahead, 0 behind).
Loop type: goal. Cloud Grok only. Reviewer follow-ups 4 to 8, then the next MVP gap that fits this lane.

## Exits (written before item work)

Binding exits from the drop-in. Check before every item. Leave 20 minutes to write the handoff.

1. Wall cap: 8 hours from launch, so 2026-11-01 09:54 UTC, or Sunday 2026-11-01 18:00 PT (PST, 2026-11-02T02:00Z), whichever comes first. The 8 hour cap binds. Stop starting a new item at 2026-11-01 09:34 UTC.
2. Lane empty: no item left that fits this lane and these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped. Record and stop.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores (64) for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail on the base before the change. Record them and skip that area. Do not stop the loop.

Eight-exit card (agent-loops), mapped onto the five above:

```text
LOOP EXIT CARD
Goal: follow-ups 4 to 8 closed or skipped with a reason, then further fitting MVP gaps, handoff written, branch pushed, not merged.
1 Goal met:                  lane empty after the listed items and any further fitting gap; handoff committed
2 Turn cap:                  one implementation pass per item; a second identical failure is exit 3
3 Budget cap:                cloud Grok only; no local model; no spend; do not run scripts/pregate.sh
4 Wall clock:                2026-11-01 09:54 UTC (handoff buffer from 09:34 UTC)
5 No-progress:               same failure twice, or 3 skips in a row
6 Human interrupt:           user stop; no question stops the loop
7 Error threshold:           same failure twice (stricter than 3)
8 External event:            item already on origin/main or on this base, or it needs an open OQ, a secret, hardware, or a local model
```

Host at start: MemAvailable 55.7 GiB. Load about 3.4 on 32 cores. GitHub `Runner.Worker` was running, so a pregate would be skipped even if the header allowed it. Targeted niced tests only.

## Plan

Overview: Close reviewer follow-ups 4 to 8 from the backlog-catalog gate at `1f3b1a3` (base already contains `2a74482`). Each item is the smallest change, one commit, one push. After those, take the next docs or test gap that fits this lane until an exit.

Phases:
- fu-4-gate-dispatch | `docs/build-dropins/common-rules.md`, `docs/ops/PREGATE.md`, `docs/ops/eval-gates-and-ux-uat.md`, `docs/ops/HANDOFF-pregate.md`, the three drop-in finish lines, `tests/test_gate_path_docs.py` | gate text requires `eval-structural` at the fix pin and both G0 jobs before a fast-forward; the test fails if that text is gone | none | general
- fu-5-shallow | `tests/test_shallow_checkout_history.py` (not `scripts/pregate.sh`) | depth-1 clone of `1f3b1a3` fails docs hygiene; depth-1 of `2a74482` passes | fu-4 | general
- fu-6-judgment-allowlist | `tests/test_catalog_stage_eval.py` | cards missing judgment fields must equal the pinned four names | none | general
- fu-7-073-unverified | `sources/entries/073-laguna-s-2-1.md`, `tests/test_laguna_smoke_note.py` | source marked content-unverified; a 200 is not recorded as verified | none | general
- fu-8-voice-facts | `tests/test_voice_stage0_ref.py`, entries 150-152 | structured facts; the guard still fails a PASS while cloud keys or a missing pin remain | none | general
- next-gap | a docs or test MVP row that fits after fu-8 | closed or skipped with a reason | fu-4 through fu-8 | general
- handoff | `docs/ops/HANDOFF-mvp-backlog-fu-1031.md`, this log | final state line, commit, push, no merge | all | general

Risks:
- `scripts/pregate.sh` is named as Run A's file in the backlog handoff, and this lane must not run that script. Item 5 uses the allowed depth-1 clone test instead, and records a cross-lane request.
- Shared gate docs. One writer in this worktree. Skip a file another 1031 lane owns.
- Depth-1 clones use local objects and scratch under this worktree `tmp/`.
- New text has no em dash and no en dash.

## Items

Format: `item | commit | tests | result`
