# Autonomous decisions: mvp-hermes-check-1031

1. 2026-11-01T01:33Z: Skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. Choice: follow the drop-in exit list, the agent-loops eight-exit card in the run log, and `docs/ops/HANDOFF-mvp-hermes-check-1031.md`. Alternative: stop and ask. Why: the drop-in already states the exits and the handoff path, and it says not to ask.

2. 2026-11-01T01:33Z: One workstream (recompute, offline check, doc fix, report). Choice: the lead does it. Do not spawn a second agent to re-derive the same numbers. Alternative: spawn a sub-agent and trust its table. Why: the definition of done is the lead's recomputation from the raw file. A sub-agent report would still have to be recomputed. `project-map` is the only spawn, and `.project-map/` is gitignored.

3. 2026-11-01T01:33Z: Pregate. Choice: do not run `scripts/pregate.sh`. Alternative: run it once at the end if the GitHub runner is idle. Why: this lane's drop-in says "Do not run scripts/pregate.sh" and that line is more specific than the shared pregate paragraph. Record "pregate not run: lane drop-in forbids scripts/pregate.sh" in the handoff.
