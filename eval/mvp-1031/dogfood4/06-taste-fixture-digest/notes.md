# 06 taste-fixture-digest

Human: accept.

Why: only `examples/x-intake-local/smoke_143_145.py` changed. `site_digest` hashes regular-file bytes and records a symlink as `link:<readlink>` without opening the target. Both `tree_hash(site)` calls in `_taste` now use `site_digest`. `tree_hash` was removed from the import. `smoke_140_142.py` and `files_under` were not edited. The gate was red (2 errors, 1 failure) before the edit and 3 OK after. Review accepted attempt 1.

Cloud commit: 43b36c88a62978d815bf3df1d8f10d148cc4970e
Landed: 538c771 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 66
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink whose target bytes match the regular file changes the digest, and the outside bytes stay. A symlink to a missing path does not raise.
Recover: a regular site tree still digests from file bytes, and the taste-skill checks still compare the snapshot to the tree after the run.

Tests after land: `tests.test_smoke_143_site_digest` and `tests.test_x_intake_smoke_143_145`, 73 OK (1 skipped).
