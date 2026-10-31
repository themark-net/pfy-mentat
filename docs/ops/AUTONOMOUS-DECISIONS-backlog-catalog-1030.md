# Autonomous decisions: backlog-catalog-1030

One line each. Choice, alternatives, why. Conservative and reversible.

- 2026-10-30 20:40 PT: The named skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. Bound the loop to the drop-in exit list, the agent-loops exit card in the run log, and `docs/ops/HANDOFF-backlog-catalog-1030.md`. Alternative was to stop and ask. The drop-in already states the exits and the handoff path.
- 2026-10-30 20:40 PT: One writer for the backlog lane. Every item updates `docs/TODO.md` and the run log, and the drop-in forbids other worktrees. Alternative was one sub-agent per catalog row. Project-map still draws gitignored `.project-map/` only.
- 2026-10-30 20:40 PT: Wall clock starts at drop-in commit `ceb3294` (2026-10-30 20:28:46 PT), so the cap is 2026-10-31 04:28 PT. Alternative was 8 hours from the first tool call. The drop-in commit is the launch record.
- 2026-10-30 21:20 PT: T-0095 issue #10 is closed on a stub that does not record the three Stage-0 legs. Wrote receipts 150-152 as FAIL / I0 from upstream docs, with no install. Alternative was to only move the TODO row. The drop-in still named T-0095, and a closed stub is not a gate an operator can re-check.
- 2026-10-30 21:20 PT: Pipecat's "under 5 minutes" headline is not a pass while that page requires Deepgram, OpenAI, and Cartesia keys. Alternative was to mark the leg shown and pass it. This run did not time or install it, and ADR-0012 keeps duplex off the primary path.
