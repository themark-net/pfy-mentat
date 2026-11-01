# Autonomous decisions: mvp3-s2s5-1031

1. Choice: treat `repo-handoff-doc-required` and `write-loop-exits-first` as the drop-in states them (exit card in the run log before item edits, handoff on every exit). Alternatives: block until those skill files appear. Why: no SKILL.md with either name is in this checkout or `~/.grok/skills`. `prefer-behavior-and-fail-recover-tests` and the orchestrator skill are present and are followed.

2. Choice: implement S2, S3, S4, and S5 in this worktree, one after another, with no implementation sub-agent. Alternatives: spawn four agents, or give each a worktree. Why: they all edit `scripts/pfy_build_local.py`. The drop-in forbids other worktrees under `tmp/` and requires a push after each item. The project-map sub-agent is the only spawn. It writes `.project-map/` only.

3. Choice: overall wall budget defaults to 7200 seconds (`--wall-timeout`, env `PFY_LOCAL_BUILD_WALL_TIMEOUT`). A hit is receipt status TIMEOUT, reason `wall-timeout`, exit 3. Alternatives: no default (flag only), or reuse `--timeout` as the whole-loop cap. Why: the bug is that the loop has no overall cap. Reusing `--timeout` would change the per-agent hang tests. 7200s covers the mvp3 t4 run (2203s) and still stops a retry loop. Recovery is a larger `--wall-timeout`.

4. Choice: an agent exit that is not 0, with an empty diff, is reason `agent-crashed` and is retryable. Exit 0 with an empty diff stays `no-change`. A non-zero exit that did write files still goes through the gate. Alternatives: label every non-zero exit as a crash, or keep no-change. Why: Tester's crash repro is `os._exit(70)` before any write, and a crash followed by a real edit must still be able to PASS.

5. Choice: a spent review rejection uses receipt status `FAIL` and reason `review-rejected`, and the summary line starts with `FAIL`. Alternatives: keep status `PASS-REJECTED`, or add `PASS-REJECTED` to the operator schema. Why: the operator receipt schema status set is `PASS|FAIL|BLOCKED|TIMEOUT|ABORTED`. This lane says the receipt label must match that set. Exit stays 1, nothing is committed, and `eval/mvp3/run_trial.py` already maps `FAIL` to reject. The mvp3 drop-in name `PASS-REJECTED` stays in the reason path only as the words reviewers already see in `review-rejected`.

6. Choice: after S5, look for the next fitting gap. Alternatives: stop because an earlier project map said to stop after S5. Why: the drop-in says keep taking the next MVP gap that fits this lane until an exit fires. The map default does not override the drop-in.

7. Choice: stop as lane empty. Alternatives: retighten the ignored-helper reason, re-kill M10/M17/M18, or edit the shared operator handoff. Why: on this base those tests and the fault-hook sentence are already present. `docs/ops/HANDOFF-pfy-local-build-mvp.md` is outside the owned set, so the stale `PASS-REJECTED` sentence is a cross-lane request, not an edit here.
