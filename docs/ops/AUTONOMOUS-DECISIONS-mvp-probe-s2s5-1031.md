# Autonomous decisions: mvp-probe-s2s5-1031

1. Choice: treat `repo-handoff-doc-required` and `write-loop-exits-first` as the drop-in states them (exit card in the run log before probe work, handoff on every exit). Alternatives: block until those skill files appear. Why: no SKILL.md with either name is in this checkout or `~/.grok/skills`. `prefer-behavior-and-fail-recover-tests`, `agent-loops`, and the orchestrator skill are present and are followed.

2. Choice: probe sub-agents stay inside this worktree and write only under `tmp/`. Branch B is a `git archive` into `tmp/cloud347-src`. Alternatives: give each phase its own `git worktree` on `build/<phase>` as the orchestrator skill prefers. Why: the drop-in forbids any other worktree under `tmp/` and forbids `git worktree` for the cloud reads.

3. Choice: edit only the larger-diff sentence in `docs/ops/HANDOFF-pfy-local-build-mvp.md`. Leave historical handoffs and `eval/mvp3/run_trial.py` alone. Alternatives: rewrite every old `PASS-REJECTED` mention. Why: the drop-in names that one sentence. Older receipts and the eval scorer still need the old status string.
