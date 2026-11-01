# Autonomous decisions mvp-cloud347-1031

- 2026-11-01T02:34:05Z | Skills `write-loop-exits-first` and `repo-handoff-doc-required` are not files in this worktree or `~/.grok/skills`. Bound the loop to the drop-in exit list, the exit card in `docs/ops/RUN-LOG-mvp-cloud347-1031.md`, and `docs/ops/HANDOFF-mvp-cloud347-1031.md`. | Stop and ask. | The drop-in says do not ask, and it already names the exits and the handoff path.
- 2026-11-01T02:34:05Z | The lead implements the three findings in order on this worktree. One project-map subagent may write `.project-map/` only. | Spawn one editor subagent per finding. | All three edit `scripts/pfy_build_cloud.py` and `tests/test_pfy_build_cloud.py`.
- 2026-11-01T02:34:05Z | Do not edit `docs/TODO.md` or `docs/OPEN_QUESTIONS.md` from this lane. Record skips and the symlink OQ in this lane's handoff. | Update the shared indexes. | Those files are shared across lanes.
- 2026-11-01T02:34:05Z | While `Runner.Worker` is present, edit code and poll. Run the targeted unittest only after `pgrep -f 'Runner[.]Worker'` is empty. | Run the suite immediately. | The drop-in G0 rule says that process shares `~/.cache/uv`.
