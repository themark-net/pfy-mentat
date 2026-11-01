# Run log: mvp-hermes-check-1031

Lane: check the Hermes eval report against raw results. Docs only. No local model.
Branch: `bot/mvp-hermes-check-1031`
Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-hermes-check-1031`
Base: `origin/bot/hermes-eval` @ `24fe672` (HEAD started at `ed1ce42`, drop-in only).
Launch: 2026-11-01T01:33:23Z
Wall cap: 2026-11-01T09:33:23Z (8 hours from launch). Sunday 2026-11-02T02:00Z is later, so the 8 hour cap binds. Stop new items by 2026-11-01T09:13:23Z to leave 20 minutes for the handoff.
Host at launch: MemAvailable about 65 GiB. Load 4.57 on 32 cores (2x cores = 64). Not under pressure.

## LOOP EXIT CARD

```text
LOOP EXIT CARD
Goal (success criteria):     Every numeric claim in the Hermes eval report is listed with claim, source file, recomputed value, and match yes/no/unverified. Wrong numbers in docs are fixed (docs only). Cheapest no-model scorer or structural check re-run. docs/ops/HERMES-EVAL-CHECK-1031.md exists. Handoff and final state line committed and pushed.
1 Goal met:                  Lead recomputes from pipelines/dogfood/hermes-bakeoff/results.json and the scorer. Offline unittest tests.test_hermes_bakeoff (no live, no local model).
2 Turn cap:                  8 items. This lane has one named item, then only MVP gaps that are docs checks of this same eval.
3 Budget cap:                Cloud Grok only. No local model. No spend. No --local. No pregate.sh.
4 Wall clock:                2026-11-01T09:33:23Z, or 2026-11-02T02:00Z, whichever comes first. Handoff buffer 20 minutes.
5 No-progress:               Same failure twice with no new information, or 3 items in a row skipped.
6 Human interrupt:           User stop. No questions. Irreversible actions stay forbidden (no merge, no force push, no tags, no PR).
7 Error threshold:           3 consecutive same failures, then stop. Drop-in also stops on 3 skipped items.
8 External event:            Stop if origin/bot/hermes-eval or origin/main already contains HERMES-EVAL-CHECK-1031.md with the same recomputation. n/a otherwise.
Loop type:                   goal
Human gate:                  No merge. Pregate plus Reviewer for this docs/eval check. Pregate only if the GitHub runner is idle at the end.
```

Drop-in exits (also checked before every item):

1. Wall cap (above).
2. Lane empty: no item left that fits this lane and these rules.
3. No progress: same failure twice, or 3 skips in a row.
4. Host pressure: MemAvailable under 16 GiB, or load over 2x cores for 5 minutes. Pause 10 minutes, then stop if it persists.
5. Red base: tests that fail on the base before this lane's change. Record and skip that area. Do not stop the lane.

## Phases

Overview: Re-derive every number in the Hermes eval write-up and handoff from the committed raw aggregate, re-run the offline bake-off tests, correct any wrong doc claim, and write the check report. One workstream. The lead does the recompute because the definition of done is the lead's own arithmetic against the raw file.

Phases:

- exit-card | docs/ops/RUN-LOG-mvp-hermes-check-1031.md, docs/ops/AUTONOMOUS-DECISIONS-mvp-hermes-check-1031.md | both files exist before the check | none | lead
- recompute | pipelines/dogfood/hermes-bakeoff/results.json (read), docs/eval/hermes-vs-current.md, docs/eval/HERMES-EVAL-HANDOFF.md, sources/entries/134-hermes-agent.md, docs/PENDING-HANDOFF.md | every numeric claim has claim, source, recomputed value, match | exit-card | lead
- offline-check | tests/test_hermes_bakeoff.py (run, not edit unless a doc claim needs a code note, and code edits are out of scope) | `nice -n 19 python3 -m unittest tests.test_hermes_bakeoff` green, no local model, no --live | recompute | lead
- doc-fix | the eval docs above, only if a claim mismatches | wrong numbers corrected, docs only, one commit | recompute | lead
- check-report | docs/ops/HERMES-EVAL-CHECK-1031.md | report committed with the claim table | recompute, offline-check | lead
- handoff | docs/ops/HANDOFF-mvp-hermes-check-1031.md, this run log final state line | handoff committed and pushed | check-report | lead

Risks:

- Raw per-task JSONL is not in git (`./tmp/bakeoff/full1/`). Mitigation: recompute from `results.json` only. Claims that need the missing transcripts or a live `ollama ps` are marked unverified, not guessed.
- A live rescore would load a local model. Mitigation: do not run `run.py --live`. Offline unittest and a pure recompute of `score.aggregate` / `margin_verdict` only.
- Other lanes share the host. Mitigation: targeted unittest, nice 19, no flock-heavy job, no pregate unless the runner is idle at the very end. This lane's drop-in also says do not run scripts/pregate.sh, so pregate is not run.
- Shared docs (`docs/PENDING-HANDOFF.md`, `docs/TODO.md`) may be owned by other lanes if they edit them. Mitigation: edit a Hermes number in those files only when this lane's check proves it wrong. If a concurrent lane already changed the file, record a cross-lane request instead of overwriting.

## Item log

| item | commit | tests | result |
|---|---|---|---|
| exit card | 54053a8 | none | written before the recompute |
| hermes-eval recompute | (this commit) | `nice -n 19 python3 -m unittest tests.test_hermes_bakeoff -v` -> Ran 9 tests in 0.658s OK | two prose claims corrected; headline numbers match; check report written |

## State lines

state: PLAN | tests: none yet | files: run log + decisions | err: none
state: DONE | tests: unittest tests.test_hermes_bakeoff 9 OK in 0.658s | files: check report + two doc corrections | err: none
