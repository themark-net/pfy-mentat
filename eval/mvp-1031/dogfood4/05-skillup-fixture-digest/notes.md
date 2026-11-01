# 05 skillup-fixture-digest

Human: accept.

Why: only `examples/x-intake-local/smoke_146_147.py` changed. `fixture_digest` hashes regular-file bytes and records a symlink as `link:<readlink>` without opening the target. `_skillup` snapshots the digest before the run and sets `fixture_unchanged` from digest equality. `term_wait_problem` and `main` were not edited. The gate was red (2 errors, 1 failure) before the edit and 3 OK after. Review accepted attempt 1.

Cloud commit: 7cebc92b635c4286cc28ce1c80df4f21c3e6507f
Landed: e6aad0d (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 131
Attempts: 1
Review: accept
Exit: 0

Fail: a byte edit of a fixture file changes the digest. A symlink whose target has the same bytes also changes the digest, and the target bytes stay. A symlink to a missing path does not raise.
Recover: writing the original bytes back restores the digest. The skill-up stub suite still passes, including the case that adds an extra fixture file.

Tests after land: `tests.test_smoke_146_fixture_digest`, `tests.test_smoke_146_term_wait`, and `tests.test_x_intake_smoke_146_147`, 41 OK.
