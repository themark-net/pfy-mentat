# Handoff: mvp-backlog-fu-1031

Status: stopped. Exit: lane empty. Branch `bot/mvp-backlog-fu-1031`, worktree `~/DEVELOP/pfy-mentat/tmp/mvp-backlog-fu-1031`, base `origin/bot/backlog-catalog-1030` at `2a74482`. Not merged. No Feature GO. Catalog HOLD 70-75 unchanged.

Cloud Grok only. No local model. `scripts/pregate.sh` was not run: this lane's drop-in forbids it, and `Runner.Worker` was active at the stop (2026-11-01 02:14 UTC, pid 1225684).

pregate not run: host busy.

## Gate

Docs, eval, and test-only changes, plus `scripts/catalog_check.py` labeling entry 073. No product runtime change. Gate: pregate plus Reviewer, after a GitHub `eval-structural` dispatch at this branch tip.

This branch adds and edits tests under `tests/`. A local pregate PASS does not replace the dispatch. Before any fast-forward, dispatch `eval-structural` (`workflow_dispatch`) at the tip SHA and wait until both G0 jobs have a conclusion on that SHA: `G0 (ubuntu-24.04)` and `G0 (self-hosted nimo)`. Do not fast-forward while either job is queued or in progress, or while the ubuntu job failed. A nimo job that ran and failed blocks the fast-forward. A nimo job that never started because the runner was offline is recorded as not run. It is not a pass. See [common-rules.md](../build-dropins/common-rules.md).

No PR. This run does not merge and does not fast-forward `main`.

## Items done

| Item | Commit | Tests | Result |
|------|--------|-------|--------|
| 4. Dispatch `eval-structural` at the fix pin and wait for both G0 jobs before a fast-forward | `443fc9d` | `tests.test_gate_path_docs` `tests.test_docs_hygiene` | 5 tests OK in 0.026s |
| 5. Depth-1 docs hygiene is red on `1f3b1a3` and green on `2a74482` | `aa7548d` | `tests.test_shallow_checkout_history` `tests.test_docs_hygiene` | 5 tests OK in 0.571s |
| 6. Pin stage cards that omit judgment fields | `5101b88` | `tests.test_catalog_stage_eval` | 5 tests OK in 0.014s |
| 7. Entry 073 source is content-unverified | `3182879` | `tests.test_laguna_smoke_note` `tests.test_catalog_entry_numbers` | 4 tests OK in 0.071s |
| 8. Voice stage0 receipts checked as facts | `145ea40` | `tests.test_voice_stage0_ref` | 2 tests OK in 0.001s |

## Skipped

No further MVP row fits this lane after items 4 to 8.

| Row | Why skipped |
|-----|-------------|
| T-0091 voice polish | Shelved. TTS and VoIP stay open until a human resumes them. |
| T-0005 stage letters | OQ-0003. Do not auto-promote. Item 6 only pins the four cards that omit judgment fields. |
| T-0062 / issue #25 Laguna lab | Needs a quant pull and a local model. This lane is cloud only. |
| T-0094 local TTS | Needs a local model. |
| T-0081 OpenCode-in-cage smoke | Cage smoke, not this lane. |
| T-0016 large-model lab | Hardware and the 250GB pool. |
| T-0046 AgenC | ADR-0010. Needs an ADR, not a drive-by edit. |
| T-0064, T-0043 | Parked env and write-guard work. |
| T-0110 G8 line still says partial | The catalog lane left that row and said not to reopen issue #76. The Done table already says done. Not flipped. |

## Test evidence

Targeted and niced. No `unittest discover`, no `make eval-*`, no `scripts/pregate.sh`.

Depth-1 proof inside `tests.test_shallow_checkout_history` (full history is present in this worktree): `1f3b1a3` fails `git cat-file` on `7197200` (`invalid object name`), and `2a74482` passes because the test returns when the clone is shallow. A depth-1 CI checkout of this branch does not contain those two pins, so that part skips there. The synthetic parent-commit probe still fails an unguarded `git cat-file`.

## How each change fails and how we recover

| Change | How it fails | Recovery |
|--------|--------------|----------|
| Gate path text | A docs pin that adds tests is fast-forwarded after pregate alone, and a depth-1 G0 job never ran the new tests | Put the both-jobs rule back. `tests.test_gate_path_docs` fails if the rule is missing. Dispatch `eval-structural` at the pin and wait. |
| Shallow history | `tests/test_docs_hygiene.py` probes an old SHA with no shallow return. Full-worktree pregate stays green. Depth-1 CI fails | Return before the probe when `git rev-parse --is-shallow-repository` is true, or stop probing objects a depth-1 checkout does not have. |
| Judgment allow-list | A new stage card omits `uses`, `features`, `potential`, `non_goals`, or `next_gate` | Fill the fields from a real handoff, or add the name to the pin only when the omission is intentional. |
| Entry 073 | The source line says verified, or `x_post_status_verdict(200, ...)` returns verified | Set the source back to content-unverified. Read the post before claiming its words. An HTTP 200 is not that reading. |
| Voice facts | `stage0` is PASS while `required_env` is non-empty or `git_pin` is null | Keep Stage-0 FAIL. Clear `required_env` only after a timed hello with no cloud account. Set `git_pin` only from a published repository. A PASS with a pin and an empty `required_env` is not blocked. |

## Cross-lane request

Run A owns `scripts/pregate.sh`. This lane did not edit it. Please add a shallow-clone check: `git clone --depth=1` of the pin into the run dir, then `tests.test_docs_hygiene` and any other test that runs `git cat-file` or `git show` on an old SHA. The same proof is already in `tests/test_shallow_checkout_history.py`.

## Next step

Reviewer on `bot/mvp-backlog-fu-1031` after `eval-structural` has been dispatched at the tip and both G0 jobs have a conclusion. Do not fast-forward from this run. Do not merge.
