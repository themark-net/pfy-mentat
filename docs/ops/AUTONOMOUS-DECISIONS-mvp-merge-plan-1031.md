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

12. Choice: cherry-pick mvp3-review-retry instead of a textual merge. Alternatives: merge and resolve the mis-aligned hunks in place. Why: a full merge paired the wrong neighbors in `scripts/pfy_build_local.py`. Cherry-pick keeps integrate-only helpers.

13. Choice: do not textual-merge mvp3-followups-1031. Alternatives: merge it after review-retry. Why: every non-merge subject is already in the cherry-pick. It is not an ancestor of integrate, so it is not safe to delete.

14. Choice: cherry-pick probe-fix2, including `915edf0` (hardlink) which landed after the first three picks. Alternatives: textual merge. Why: a textual merge repeats the review-retry conflicts. The hardlink commit applied clean onto the review-timeout fix.

15. Choice: crosslane code hunks stay with HEAD. Alternatives: take crosslane's pathspec order and its missing-file status. Why: on git 2.53 an exclude after a positive pathspec drops an untracked path. A missing out file must be `review-crashed`, not a status that retries.

16. Choice: docs-final wins the QUICKSTART body, and the intro keeps the walkthrough link. Alternatives: keep the earlier docs-1031 card. Why: docs-final is the later measured card (`--writable-test`, stricter `--base`, runnable fence).

17. Choice: dogfood2 `tree_sig` is a union (symlink hash, size, streamed sha256, no mtime). smoke_148 `home_sig` stays mtime-sensitive. smoke_149 stays mtime-ignorant. Alternatives: take either side whole. Why: dropping size or mtime on smoke_148 would hide a real-HOME change the stricter test asserts.

18. Choice: fix the two cherry-pick union bugs in scratch commit `b8d9b64` before later merges. Alternatives: record the two mvp3 failures and leave them. Why: a review timeout was classified as `crashed`, and a duplicate `warnings` key dropped the allow-list warning. Both are fail-closed bugs, and the rerun passed.

19. Choice: dsv4 TODO conflict keeps the integrate section. Alternatives: take dsv4's TODO. Why: same policy as mvp3. Incoming catalog files auto-merged. Do not copy the TODO hunk onto this lane.

20. Choice: mutate-cloud2 wins the add/add of `run_mutants.py` and the results JSON. Alternatives: keep mutate-cloud's shorter harness. Why: cloud2 contains C1-C16 and C17-C43. A clean preview went stale once mutate-cloud had created the same paths.

21. Choice: plan-1031 add/add of `docs/build-dropins/mvp-integrate-1031.md` keeps HEAD (pass 2 and pass 3 addenda). Alternatives: take the original drop-in. Why: theirs was empty at that region. The later operator addenda are the ones integrate already shipped.

22. Choice: timeoutfix union keeps commit-then-overlap and adds the run budget. Both recheck tests stay. On review timeout, undo the commit before `as_reject`. Alternatives: take theirs' direct `grok_call`, or drop the budget. Why: theirs does not bind `review_row`, and `as_reject` does not undo a commit that HEAD already made.

23. Choice: when a tip moved after its merge, merge the new subjects. Alternatives: freeze at the first merge. Why: dogfood3, probe-fix2, selfhost2, timeoutfix, and cloud-perf pushed during the run. A subject scan at 2026-11-01T01:20:48Z found no missing subject except this lane.

24. Choice: one end batch of targeted tests at scratch `9b63b93`, then reruns after the expectation fix and the late retips. Alternatives: a full module run after every merge. Why: a later merge edits files an earlier test imported. Each plan row cites the SHA the test actually ran against. The cloud suite was not re-cited from the pre-timeoutfix log.

25. Choice: leave the four stale anchor and planted-diff failures red. Alternatives: regenerate mutant catalogs or revert the runner so old patches apply. Why: the harness is fail-closed when the anchor is gone. Regenerating the catalog is a new scoring pass, not a merge resolution. The recovery is in the plan.

26. Choice: scratch commit `52e3ddc` updates tests to the winning runner. Alternatives: leave the phase-clock and first-day tests red. Why: they encoded "extract has no `.git`" and the looser `--base` help. The nested recheck repo and the docs-final help are the winners. The rerun passed.

27. Choice: stop the retip chase at freeze `cee9bdd` / 2026-11-01T01:20:48Z. Alternatives: keep merging until the wall cap. Why: the subject scan was empty. Further lane pushes belong in a fetch immediately before the real landing, which the plan names as the next step.
