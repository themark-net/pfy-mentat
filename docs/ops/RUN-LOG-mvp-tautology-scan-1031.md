# RUN-LOG mvp-tautology-scan-1031

Lane: `bot/mvp-tautology-scan-1031`
Worktree: `/home/mark/DEVELOP/pfy-mentat/tmp/mvp-tautology-scan-1031`
Base: `origin/bot/mvp-integrate-1031` at `1dee0b91bda11ba1fcda87819423437a3f10f289`
Launch: `2026-11-01T02:34:15Z`
Head at plan: `6b648891125db727addca16b4783a07aaef43fd5` (drop-in only; matches origin)

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     docs/ops/TAUTOLOGY-SCAN-1031.md lists file, test, why it is tautological, and the fix, after a line-by-line read of eval/ and tests/. The worst owned cases are replaced with a behavior or fail/recover test, or deleted when a behavior test already covers them. Each replacement was proved by a mutation that turned the test red, then restored. Live-lane tests were not edited.
1 Goal met:                  the scan doc is committed, each fix commit names the item, targeted tests passed, and the handoff lists SHAs. Pregate plus Reviewer is the gate. This lane does not run pregate.
2 Turn cap:                  8 fix items after the scan doc. Further MVP gaps in this lane stop at the cap.
3 Budget cap:                cloud Grok only. No local model. No spend beyond this session. Never pass --local.
4 Wall clock:                8 hours from launch, so 2026-11-01T10:34:15Z, which is before Sunday 2026-11-02T02:00Z. Stop new items at 2026-11-01T10:14:15Z and use the last 20 minutes for the handoff.
5 No-progress:               the same failure twice with no new information, or 3 items in a row skipped.
6 Human interrupt:           do not ask. User stop is the kill switch. Irreversible actions stay inside the pre-authorized list (commit and push this branch only).
7 Error threshold:           3 consecutive same failures, then stop. A red base is recorded and that area is skipped. It does not stop the lane.
8 External event:            a live lane owns the file, or origin already fixed that test. Skip and record a cross-lane request. n/a for merge (this lane does not merge).
Loop type:                   goal
Human gate:                  pregate plus Reviewer. No merge, no PR, no tag.
```

Drop-in exits (checked before every item):

1. Wall cap: 2026-11-01T10:34:15Z, or Sunday 2026-11-02T02:00Z, whichever comes first. The 8 hour cap comes first. Handoff buffer starts 2026-11-01T10:14:15Z.
2. Lane empty: no remaining tautology this lane may edit, and no next MVP gap that fits these rules.
3. No progress: the same failure twice with no new information, or 3 items in a row skipped.
4. Host pressure: MemAvailable under 16 GiB, or load over 64 (2 x 32 cores) for 5 minutes. Pause 10 minutes, then stop if it still holds.
5. Red base: tests that fail on the base before this lane's change. Record them and skip that area.

Host at plan (`2026-11-01T02:34:15Z`): MemAvailable 56606856 KiB (about 54 GiB). Load 3.33, 3.38, 3.85 on 32 cores. Under both pressure lines.

G0: `Runner.Worker` pid 1511538 is present. Do not run uv, `./pfy`, or any python test suite until `pgrep -f 'Runner[.]Worker'` is empty. Poll every 60s before a test. Read and edit may proceed. Do not run `scripts/pregate.sh`.

Named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. This card, the drop-in exit list, and `docs/ops/HANDOFF-mvp-tautology-scan-1031.md` are the binding. `prefer-behavior-and-fail-recover-tests` is present and is the rubric.

## Plan

Overview: Pass 3 review left 389 `eval/` paths unread line by line, and did not read every test module, so a tautological test can still exist. This lane reads `eval/` and `tests/` against the behavior-test skill, writes the scan table, then fixes the worst owned cases and proves each fix with a mutation.

Phases:

- exits | `docs/ops/RUN-LOG-mvp-tautology-scan-1031.md`, `docs/ops/AUTONOMOUS-DECISIONS-mvp-tautology-scan-1031.md` | exit card and phase plan committed before the scan | none | lead
- scan-eval | `eval/` | line-by-line notes under `tmp/tautology-scan/eval.md` | exits | general, read-only
- scan-tests-a | `tests/` from `test_agentdescent_trial_harness.py` through `test_home_sig_doc.py` | notes under `tmp/tautology-scan/tests-a.md` | exits | general, read-only
- scan-tests-b | `tests/` from `test_jev_decision_skill.py` through `test_pfy_local_build_eval.py` | notes under `tmp/tautology-scan/tests-b.md` | exits | general, read-only
- scan-tests-c | `tests/` from `test_registry.py` through `test_x_intake_smoke_149.py` | notes under `tmp/tautology-scan/tests-c.md` | exits | general, read-only
- report | `docs/ops/TAUTOLOGY-SCAN-1031.md` | table of file, test, why, fix | scan-eval, scan-tests-a, scan-tests-b, scan-tests-c | lead
- fix-worst | owned test or checker files named in the table, at most 8 | each fix is a behavior or fail/recover test, or a deletion when coverage already exists; a mutation turns it red, then the code is restored | report, and Runner.Worker absent | lead
- handoff | `docs/ops/HANDOFF-mvp-tautology-scan-1031.md` and the final `state:` line in this log | committed and pushed | fix-worst or an exit | lead

Risks:

- The GitHub runner shares `~/.cache/uv`. Mitigation: no uv, `./pfy`, or python test suite while `Runner.Worker` is present. Mutation proof waits on the poll.
- Live lanes own `tests/test_pfy_build_local.py`, `tests/test_pfy_build_local_review.py`, `tests/test_pfy_build_local_review_ci.py`, `tests/test_pfy_build_cloud.py`, and `tests/test_harness2_local_stage.py`. Mitigation: scan them, do not edit them, record a cross-lane row.
- Rewriting `eval/local-build/fixtures/` would change scored tasks and historical receipts. Mitigation: document fixture tautologies and do not edit those task tests.
- Four readers plus the lead share one worktree. Mitigation: scan agents write only their notes file under `tmp/tautology-scan/`. The lead writes `docs/ops/`. No second worktree.
- Another branch may already have fixed a case. Mitigation: `git fetch` done at plan time. Before each fix, check `origin/main` and this base.

## Item log

Clock check before exits: `2026-11-01T02:34:15Z`, inside the cap. MemAvailable 56606856 KiB. Load 3.33 on 32 cores. Runner.Worker present.
