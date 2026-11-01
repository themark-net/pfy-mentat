# 02 attach-session-symlink

Human: accept.

Why: `read_session_reach` returns an empty string when the session file is a symlink and does not read the target. `write_session_reach` uses `_write_regular_text`, which `os.replace`s a temp file onto the path. Only `pfylib/attach.py` changed (20 insertions, 1 deletion). `write_terminal_pid`, `clear_session_reach`, and `_write_spawn_receipt` are untouched. The gate was red before (exit 1, 3 failures) and 4 tests OK after. Review accepted attempt 1. After land, `tests.test_attach_session_symlink` and `tests.test_attach` together were 38 OK.

Cloud commit: ba92aca780cb3d447b8b014159ed8741b649bab1
Landed: 29ee1cc (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 167
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at the session file leaks the target text on read and is overwritten on write. A broken symlink creates the missing target.
Recover: a regular session file still round-trips the trimmed text. After a replace, read returns the new text.

Tests after land: `tests.test_attach_session_symlink` and `tests.test_attach`, 38 OK.
