# 02 modules-symlink

Human: accept.

Why: only `pfylib/loop_paint.py` changed. `load_selection` returns the empty selection when the path is a symlink and does not read the target. `save_selection` writes through `_put_text`, which uses `os.replace`, so the symlink becomes a regular file. `toggle` and the stub copy string were not edited. The gate was red (3 failures) before the edit and 4 OK after. Review accepted attempt 1.

Cloud commit: 01597623dcc67b8fe0096eec7fd644fa2fdf618a
Landed: 2e8d20e (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 72
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at loop-modules.json is not read, and save replaces it. A broken symlink does not create the missing target. The outside file stays byte for byte.
Recover: a regular loop-modules.json still round-trips through save and load.

Tests after land: `tests.test_loop_paint_symlink` and `tests.test_loop_paint`, 11 OK.
