# 01 hermes-driver-symlink

Human: accept.

Why: `_write` and `_config` go through `_write_text`, which writes a temp file in the parent and `os.replace`s it onto the path. A symlink becomes a regular file. The target bytes stay. Only `pfylib/hermes_bot_driver.py` changed (18 insertions, 2 deletions). The gate was red before the edit (exit 1, 3 failures) and 4 tests OK after. Review accepted attempt 1.

Cloud commit: b011907ff97eb68a83404d090e3726d5b2589dfb
Landed: ebb808d (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 131
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at the out path or at `config.yaml`, including a broken link, no longer receives `write_text`. The outside file stays. A broken link does not create the missing target.
Recover: a regular file still receives the JSON or the config text.

Tests after land: `tests.test_hermes_driver_symlink`, 4 OK.
