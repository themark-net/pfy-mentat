# Handoff: mvp-hermes-check-1031

Lane: check the Hermes eval report against `pipelines/dogfood/hermes-bakeoff/results.json`. Docs only. No local model.
Branch: `bot/mvp-hermes-check-1031`
Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-hermes-check-1031`
Base: `origin/bot/hermes-eval` @ `24fe672`
Exit: lane empty. The named check is done. Nothing else in this lane fits the rules (no local model, docs only, no new architecture).

## Items done

| Item | SHA | What |
|---|---|---|
| Exit card and decisions | `54053a8` | Run log with the eight exits and the phase plan. Three decisions. |
| Hermes eval recompute | `a084a38` | `docs/ops/HERMES-EVAL-CHECK-1031.md`. Two prose corrections. Headline numbers unchanged. |

## What the check found

`score.aggregate` on the raw rows matches the stored `summary` for every key. Verdict stays NO-WIN. Task success 26/27 vs 25/27 (+3.70 pp). Valid tool-call rate 38/46 vs 45/46 (minus 15.2 pp). Wilson intervals overlap. Latency p50 8.75s vs 47.38s. Agent peak 221 MiB vs 1.04 GiB. Meta calls 52. Full table, with match yes / no / unverified, is in the check report.

Corrected:

- The labels stamp `2026-10-19T18:00:00Z` is later than `meta.started` `2026-10-19T08:33:09Z`, and the tasks file lands in the same commit as the results (`b48d634`). The docs no longer say that stamp proves the labels were fixed before the run.
- "+10 points means about three more baseline misses" was wrong. Two more baseline misses, Hermes still at 26/27, is 11.11 pp. One more miss is 7.41 pp.

## Items skipped

| Item | Why |
|---|---|
| Live rescore, `run.py --live`, any Ollama call | This lane must not run a local model. |
| `scripts/pregate.sh` | The lane drop-in says not to run it. More specific than the shared "if the runner is idle" line. Pregate not run: lane drop-in forbids scripts/pregate.sh. |
| pytest `-m "not live"` | `python3 -m pytest` has no pytest module. Unittest covered the 9 offline tests. The pytest sentence stays unverified as an execution. |
| 14-of-20 mutant replay | No mutant list in the tree. Building one would be new test code, and this lane's fixes are docs only. |
| Hermes wiring, meta-tools-off re-run | Needs a local model and a product change. The founder decision already says wiring is a separate change. Not this lane. |
| `docs/TODO.md` | Shared with other lanes. This check has no T-id. Left untouched. |

## Test evidence

`nice -n 19 python3 -m unittest tests.test_hermes_bakeoff -v`

`Ran 9 tests in 0.658s` `OK` (2026-11-01T01:39Z). ResourceWarnings on an unclosed socket and two unclosed pipes in the fail-closed checks. Those warnings were already the base. Tests passed. Not a red base.

No full `unittest discover`, no `make eval-*`, no docker, no pregate.

## How the change fails and recovers

Docs only. No new test, because the drop-in limits fixes to docs and a new unit test would only restate `score.aggregate`.

Failure: a reader uses `labels_written` as proof the labels preceded the scored calls, or uses "about three more misses" as the +10 pp gap. Recovery: the corrected sentences show both clocks and the one-miss / two-miss counts. The check report is the record. If a later edit drifts a headline number, re-run `score.aggregate` on `results.json` `rows` and compare to the table. A mismatch is the failure. The recovery is to correct the doc, not the raw file, unless a new scored run replaces `results.json`.

## Cross-lane requests

None. `docs/PENDING-HANDOFF.md` and `sources/entries/134-hermes-agent.md` already match the recomputed headline numbers, so they were not edited.

## Gate

Docs and eval check only. No runtime change. Gate: Reviewer. Pregate was not run (lane drop-in forbids `scripts/pregate.sh`). Do not merge from this run. Do not open a PR from this run.

## Next

Reviewer reads `docs/ops/HERMES-EVAL-CHECK-1031.md` and the two prose edits in `a084a38`. A meta-tools-off re-run stays a separate lane that is allowed to load a model. Do not treat the unverified isolation sentences (home snapshot, later `ollama ps`, 14 mutants, pytest execution) as re-proven.
