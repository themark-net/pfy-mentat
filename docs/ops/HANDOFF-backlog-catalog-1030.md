# Handoff: backlog-catalog-1030 (2026-10-30 PT)

Status: launched. Headless Grok Build (cloud Grok only) runs the drop-in `docs/build-dropins/backlog-catalog-1030.md` on branch `bot/backlog-catalog-1030`, worktree `~/DEVELOP/pfy-mentat/tmp/backlog-catalog-1030`. Pid in `tmp/backlog-catalog-1030-run.pid`, log in `tmp/backlog-catalog-1030-run.log` (both under the worktree's gitignored tmp/).

## Why

Mark asked for more throughput while MVP-3 run 2 times a local model trial: a long orchestrator loop that uses cloud Grok only and never loads a local model.

## How it fails and how we recover

| Risk | How it fails | Recovery |
|------|--------------|----------|
| CLI ends early | grok exits before the loop does | Launched with `--background-wait-timeout 14400`; relaunch from the run log's last item |
| Skews MVP-3 timing | heavy CPU while the trial runs | Targeted niced tests only while MVP-3 is busy; full suite and pregate under a shared flock only when it is idle |
| Collides with the other run | both edit the same files | Lanes are split: Run A code follow-ups, Run B catalog and docs |

## Next step

The run replaces this section with items done, skipped, evidence and the gate needed. Do not merge from the run.
