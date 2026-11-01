# 03 opencode-config-symlink

Human: accept.

Why: only `pfylib/bot_interface.py` changed. `write_opencode_config` writes through `_put_text`, which uses `os.replace`, so a symlink at opencode.json becomes a regular file and the target bytes stay. `opencode_config` and `run_opencode` were not edited. The gate was red (2 failures) before the edit and 3 OK after. Review accepted attempt 1.

Cloud commit: c908d1c55be352bf028596a20c53b9a5c3cf488b
Landed: d2dc658 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 63
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at the opencode config path is replaced, and a broken symlink does not create the missing target. The outside file stays byte for byte.
Recover: a regular opencode.json still receives the provider JSON for the given base URL and model.

Tests after land: `tests.test_bot_interface_opencode_symlink` and `tests.test_bot_interface`, 22 OK.
