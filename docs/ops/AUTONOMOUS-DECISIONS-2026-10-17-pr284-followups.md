# Autonomous decisions — pr284-followups — 2026-10-17

One line per choice. Format: choice | alternatives | why

- Lead runs the 12 items in order in this worktree | spawn one implementer per item in extra worktrees | the items share smoke.py and the smoke tests, the owner allows only this worktree, and the host stays light (no parallel full suites)
- Keep origin/main 0d574f0 as the base | merge or rebase onto origin/build/orch-fixes-1011-recheck | the owner said the base stays origin/main; read that branch's diff and do not undo d78aa15 when editing the same lines
- Do not add a TODO row for this drop-in | add T-id rows to docs/TODO.md | the queue is this drop-in plus the handoff; TODO is the product queue and these items are already specified
