# 04 attach-receipt-symlink

Human: accept.

Why: `_write_spawn_receipt` calls the existing `_write_regular_text` helper and still swallows `OSError`. Only `pfylib/attach.py` changed (1 insertion, 1 deletion). Session reach and the pid file are untouched. The gate was red before (exit 1, 2 failures) and 4 tests OK after. Review accepted attempt 1. After land, the receipt, pid, session, and attach modules together were 46 OK.

Cloud commit: 8bce3dbe0cb4bc63550c283e3ac4db82db4c6b9b
Landed: 1c100a5 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 78
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at `<sid>-attach-receipt.json` is overwritten, and a broken symlink creates the missing target.
Recover: a regular file still receives the JSON receipt. A path whose parent cannot be created still returns without raising.

Tests after land: `tests.test_attach_receipt_symlink`, `tests.test_attach_pid_symlink`, `tests.test_attach_session_symlink`, and `tests.test_attach`, 46 OK.
