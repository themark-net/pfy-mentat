# Autonomous decisions: mvp-merge-plan-1031

One line each. Choice, alternatives, why. Pre-authorized: do not ask.

1. Choice: follow `repo-handoff-doc-required` and `write-loop-exits-first` as the drop-in states them (handoff on every exit, eight-exit card in the run log before scratch merges) plus `.grok/skills/agent-loops`. Alternatives: stop until those skill files exist. Why: no `SKILL.md` with either name is in this checkout or `~/.grok/skills`. `prefer-behavior-and-fail-recover-tests` is present and is followed. The plan is docs, so no new unit tests are added for the markdown itself.

2. Choice: the integration branch is `origin/bot/mvp-integrate-1031`. Merge `origin/bot/mvp-intfix-1031` immediately after it. Alternatives: treat intfix as an alphabetical other. Why: integrate is 0 behind origin/main (fast-forward). intfix has one commit not in integrate, `1c64e50`, and that commit only adds the intfix handoff docs. The name is an integration fix.

3. Choice: mvp3 order is `origin/bot/mvp3-review-retry` then `origin/bot/mvp3-followups-1031`. Alternatives: merge followups first. Why: followups tip `ffce7a7` is an ancestor of review-retry tip `d2521b5`, so one conflict resolution covers both. followups is not an ancestor of integrate, so it is not in the safe-to-delete list.

4. Choice: do not test-merge `origin/bot/mvp-merge-plan-1031` onto the scratch stack. Alternatives: merge this lane into the stack. Why: this branch is the document destination. The stack is not pushed. Merging it would only copy the drop-in into an unpushed tree.

5. Choice: do not run `scripts/pregate.sh`. Alternatives: run it once at the end because the runner worker was idle at plan time. Why: the lane drop-in says "Do not run scripts/pregate.sh". The later "at most once" sentence does not override that prohibition.

6. Choice: `git fetch origin` only. Alternatives: `git fetch --all`. Why: the bot branches live on origin. Fetching other remotes in the shared git dir is outside this lane.

7. Choice: a tip that `git merge-base --is-ancestor` says is inside integrate is recorded as already contained and is not merged again. Alternatives: run `git merge` for each and keep the "Already up to date" output. Why: an ancestor merge does not change the tree, so there is no conflict and no touched module. The ancestor bit is the evidence. Safe to delete later means that list. Do not delete.

8. Choice: scratch stack is a detached worktree at `tmp/merge-scratch`. No local branch is pushed. Conflict commits stay in that worktree. Alternatives: commit the merges onto `bot/mvp-merge-plan-1031`. Why: the drop-in allows only `docs/ops/MERGE-PLAN-1031.md` plus the resolution notes to be pushed. The notes live in that file and in this decisions log.

9. Choice: conflict policy. Fast-forward when origin/main is an ancestor. On a content conflict, combine both sides when the hunks add different fail-closed behavior or different tests. On a true line clash in shared code (`scripts/`, `tests/`, `examples/`), keep the side that preserves the stricter check, then run that module's tests. On a clash in `docs/TODO.md` or another shared doc, keep integrate's wording and fold in incoming rows that integrate does not already state. On a lane-owned file (`docs/ops/HANDOFF-<lane>.md`, `RUN-LOG-<lane>.md`, `AUTONOMOUS-DECISIONS-<lane>.md`, `docs/build-dropins/<lane>.md`), keep the incoming lane's version. Add/add of the same path: keep integrate when the incoming file is an older drop-in, and say so. Alternatives: always take incoming, or always take integrate. Why: integrate already synthesized most lanes. Incoming unique commits are the only new facts. Dropping a fail-closed check would hide a bug the side lane fixed.

10. Choice: the lead runs the merges. The only sub-agent is `project-map`, which writes gitignored `.project-map/`. Alternatives: one sub-agent per branch. Why: the stack is ordered and shares one worktree. Sub-agents must not push and must not touch other lanes' checkouts.

11. Choice: do not edit `docs/TODO.md` on this lane's branch. Alternatives: land the TODO conflict resolution here. Why: TODO is shared with other lanes. The scratch resolution is described in the plan. A TODO edit on this branch would be a cross-lane write.
