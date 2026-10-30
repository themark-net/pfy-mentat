# Handoff: MVP-3 review-and-retry loop for `./pfy build --local`

Branch `bot/mvp3-review-retry`, base `bot/mvp2-report` 85c53dc (origin/main 1e99251 plus the MVP-2 report). Worktree `~/DEVELOP/pfy-mentat/tmp/mvp3` on nimo. No PR; Mark merges after gates.

## Status (2026-10-30 PT, Grok Bot)

Drop-in written: `docs/build-dropins/pfy-local-build-mvp3.md`. Headless Grok Build launched on nimo in this worktree with the drop-in as its prompt; pid in `tmp/mvp3-run.pid`, log in `tmp/mvp3-run.log` (gitignored, inside the worktree). The Build run overwrites this file's status with its own results when it finishes.

## Why

MVP-2 closed as a no-go for local-as-default: local gate 5/6, review 4/6, 1694 s vs cloud 6/6, 6/6, 584 s. Local t4 was green but too broad; local t5 never set `PFY_SMOKE_RECEIPT_DIR` in both test modules. The trial found that the local path lacks a review step and never got a retry after a reject.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|--------------|----------|
| Build run hangs or the host runs low on memory | The drop-in's exits stop it (3 h cap, memory floor, lockup signs) and the run log says why | Read `docs/ops/RUN-LOG-mvp3-review-retry.md`; re-running the same prompt resumes from the run log |
| Run dies without a handoff | `tmp/mvp3-run.pid` is dead and this file still says "launched" | Check the `tmp/mvp3-run.log` tail and pushed commits; relaunch with the same command |
| Reviewer too strict or too loose | Many PASS-REJECTED, or t4/t5 still accepted | The receipts name each check; tune defaults or use `--no-review` |

## Next step

When the run exits: read the report and handoff, then gate (runtime change: Tester plus Reviewer at the pinned SHA, plus pregate).
