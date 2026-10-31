# Autonomous decisions pfy-followups-1030

Run A on `bot/pfy-followups-1030`. No questions asked. One line per decision.

1. Choice: the lead executes every item in this worktree, in order, and does not spawn implementation sub-agents. Alternatives: parallel sub-agents on `build/<phase>` worktrees, or shared-checkout sub-agents. Why: the request forbids other worktrees, requires a push of this branch after every item, and the run log, TODO, and handoff are shared files.

2. Choice: follow `repo-handoff-doc-required` and `write-loop-exits-first` as the drop-in already states them (handoff doc on every exit; exit card in the run log before item work) plus `.grok/skills/agent-loops`. Alternatives: block until those skill files appear. Why: no `SKILL.md` with either name is in this checkout or `~/.grok/skills`. `prefer-behavior-and-fail-recover-tests` is present and is followed.

3. Choice: item 1 (MVP-2 reviewer follow-ups) gets prose edits only, with no new test module. Alternatives: a string-match unit test over the handoff. Why: that test would restate the prose and is the tautological kind the behavior skill forbids. Docs-only changes have no code path to fail.

4. Choice: add a `Known gaps` section to `docs/ops/HANDOFF-mvp2-trial.md` for the prove-red receipt gap. Alternatives: bury the gap in the existing Commands section only. Why: the reviewer named "Known gaps" and the file had no such section.
