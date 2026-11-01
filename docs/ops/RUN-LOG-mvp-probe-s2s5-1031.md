# Run log: mvp-probe-s2s5-1031

Launch: 2026-11-01T02:52:01Z
Wall cap: 2026-11-01T10:52:01Z (8 hours from launch). The Sunday cap 2026-11-02T02:00Z is later, so the 8 hour cap wins. Stop new items by 2026-11-01T10:32:01Z so the handoff has 20 minutes.
Branch: `bot/mvp-probe-s2s5-1031`
Base: `origin/bot/mvp3-s2s5-1031` at `493935b` (this branch is that commit plus drop-in `1ac17c1`)
Cloud pin: `origin/bot/mvp-cloud347-1031` at `9d75395`
Needs a local model: no. Cloud Grok only. Never `--local` as a model switch. `./pfy build --local` is the product command under test on branch A.

Host at plan: MemAvailable about 44 GiB. Load about 3.7 on 32 cores. `Runner.Worker` absent, so targeted tests are allowed. Recheck the runner before every test batch. Do not run `scripts/pregate.sh`.

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     PROBE-s2s5-cloud347-1031.md has a probe, expected, actual, and verdict for each S2-S5 fix and each cloud347 fix. Every real defect on branch A is fixed here with a red-first behavior test, committed, and pushed. Branch B defects are cross-lane repros only. HANDOFF-pfy-local-build-mvp.md no longer calls a larger diff PASS-REJECTED.
1 Goal met:                  probe doc committed, A defects green on targeted tests, B defects recorded not edited, doc sentence updated, handoff written
2 Turn cap:                  8 item iterations after the exit card (a probe batch counts as one)
3 Budget cap:                cloud Grok only; no local model; no spend beyond this session
4 Wall clock:                2026-11-01T10:52:01Z, handoff buffer from 10:32:01Z
5 No-progress:               same failure twice with no new information, or 3 items skipped in a row
6 Human interrupt:           user stop. No question stops. Conservative choice goes in the decisions file.
7 Error threshold:           3 consecutive same failures, then stop that item and record it
8 External event:            n/a (do not merge; do not wait on another lane)
Loop type:                   goal
Human gate:                  no merge, no PR. Tester plus Reviewer after runtime commits. Pregate plus Reviewer after docs-only commits. Operator runs pregate.
```

Drop-in exits, checked before every item:

1. Wall cap: clock above, leave 20 minutes.
2. Lane empty: listed probes and the doc sentence are done, and no further MVP gap fits these rules.
3. No progress: same failure twice, or 3 skips in a row.
4. Host pressure: MemAvailable under 16 GiB, or load over 64 for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail before the change. Record and skip that area. Do not stop the lane.

## Overview

Adversarial CLI probes of two fresh branches before the real gate. Branch A is already in this worktree (S2 wall budget, S3 agent-crashed, S4 review-rejected FAIL, S5 stale worktree prune). Branch B is read with `git show` or a scratch tree under `tmp/`, never a second git worktree. Real breaks on A get a red-first test and a fix here. Breaks on B are repros only. The operator handoff sentence that still says PASS-REJECTED is updated to FAIL with reason review-rejected.

## Phases

- exit-card | docs/ops/RUN-LOG-mvp-probe-s2s5-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-probe-s2s5-1031.md | both files exist and the card is above | none | lead
- probe-a | tmp/probe-a-findings.md only (read scripts/pfy_build_local.py and tests/test_pfy_build_local*.py) | each S2-S5 edge has expected, actual, verdict | exit-card | general
- probe-b | tmp/cloud347-src (git archive), tmp/probe-b-findings.md | each cloud347 fix has expected, actual, verdict | exit-card | general
- doc-sentence | docs/ops/HANDOFF-pfy-local-build-mvp.md | the larger-diff sentence says FAIL reason review-rejected | exit-card | lead
- probe-doc | docs/ops/PROBE-s2s5-cloud347-1031.md | committed report of both probe batches | probe-a, probe-b | lead
- fix-a | scripts/pfy_build_local.py and the matching test module, only for confirmed defects | red-first test, then green, one commit and push per defect | probe-doc | lead
- handoff | docs/ops/HANDOFF-mvp-probe-s2s5-1031.md and the state line in this log | exit recorded, pushed | all prior | lead

probe-a and probe-b share no product files. They run together. The doc sentence shares no files with the probe scratch trees. fix-a waits until a defect is confirmed.

## Risks

- Runner.Worker returns and shares ~/.cache/uv. Mitigation: pgrep before every python batch; if present, stop tests and poll 60s.
- A probe deletes the wrong worktree via symlink resolve. Mitigation: probes use a temp repo under tmp/scratch, never the main checkout, and assert the outside sentinel still exists.
- Branch B code is not in this tree. Mitigation: git archive into tmp/cloud347-src. Do not edit scripts/pfy_build_cloud.py anywhere. Do not register a git worktree.
- Parallel lanes. Mitigation: product edits stay in pfy_build_local.py, its tests, this lane's docs/ops files, and the one named handoff sentence.

## Items

(none yet)
