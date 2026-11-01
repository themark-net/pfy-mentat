# 04 smoke137-timeout attempt 1

Human: not cherry-picked. The runner did not keep a branch.

Why: both attempts passed the worktree gate and review accepted. `recheck_sha` extracts a fresh archive, which has no `tmp/` directory. The planted test passed `dir=ROOT / "tmp"` to `TemporaryDirectory` without creating that directory, so setUp raised `FileNotFoundError`. The runner reset the commit (`commit-recheck-failed`).

Failure class: test scratch directory missing on the fresh extract.

Cloud commit: none
Wall seconds: 296 (2026-11-01T01:53:04Z to 2026-11-01T01:58:00Z)
Attempts: 2
Review: accept, accept
Exit: 1
Gate before: 1
Gate after: 0

The live attempt diff imported `timeout_problem` from `smoke_140_142`, added the docstring sentence, and returned 2 from `main` before the entry. `tree_hash` was not in that diff. The branch was deleted by the runner, so this folder has no `diff.patch`.

Retry: the test creates `ROOT / "tmp"` in setUp, then the same task runs again.
