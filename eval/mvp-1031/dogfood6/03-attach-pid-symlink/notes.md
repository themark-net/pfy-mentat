# 03 attach-pid-symlink

Human: accept.

Why: `read_terminal_pid` returns 0 when the pid file is a symlink and does not read the target. `write_terminal_pid` uses the existing `_write_regular_text` helper. No second helper. Only `pfylib/attach.py` changed (3 insertions, 1 deletion). Session reach and the spawn receipt are untouched. The gate was red before (exit 1, 3 failures) and 4 tests OK after. Review accepted attempt 1. After land, the pid, session, and attach modules together were 42 OK.

Cloud commit: 8d7b20e769e774759cb8a4a23a2338a486bdc9d0
Landed: 3675945 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 82
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at the pid file returns the target integer on read and is overwritten on write. A broken symlink creates the missing target.
Recover: a regular pid file still round-trips the integer. A non-integer regular file still returns 0.

Tests after land: `tests.test_attach_pid_symlink`, `tests.test_attach_session_symlink`, and `tests.test_attach`, 42 OK.
