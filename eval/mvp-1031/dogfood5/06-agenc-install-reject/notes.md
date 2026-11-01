# 06 agenc-install-tmp attempt 1

Human: reject. The runner kept cloud commit 4def314cd67a10d906153f44a3d32eaeda3d5143 on the throwaway clone. It was not cherry-picked.

Why: review accepted and the worktree gate went from exit 1 to exit 0, but the diff deletes `mkdir -p "$NODE_CACHE"` and only creates the tarball directory. When TMPDIR is set, `tar -C "$NODE_CACHE"` then has no directory. The planted test stopped at the fake curl, so it did not see that.

Failure class: extract directory dropped.

Cloud commit: 4def314cd67a10d906153f44a3d32eaeda3d5143
Landed: none
Wall seconds: 121
Attempts: 1
Review: accept
Exit: 0
Gate before: 1
Gate after: 0

Retry: the test requires NODE_CACHE to exist, and the task says to keep `mkdir -p "$NODE_CACHE"` plus the tarball directory.
