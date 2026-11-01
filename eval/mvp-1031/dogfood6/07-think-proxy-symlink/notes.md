# 07 think-proxy-symlink

Human: accept.

Why: `write_forced_log` writes through `_write_regular_text`, which `os.replace`s a temp file onto the path. Only `examples/hermes-bakeoff/think_proxy.py` changed (18 insertions, 1 deletion). `path.parent.mkdir` stays. `json.dumps` stays `sort_keys=True`. A non-empty list still ends with one newline, and an empty list still writes an empty file. `force_chat_body` and `ThinkProxy` are untouched. The gate was red before (exit 1, 2 failures) and 3 tests OK after. Review accepted attempt 1. After land, `tests.test_think_proxy_symlink` and `tests.test_hermes_bakeoff` were 35 OK (1 skipped). The post-land run waited until the GitHub runner was gone.

Cloud commit: 49979f196748f86fc730507f8f4706f0ed7a0424
Landed: 4340a72 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 87
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at the log path, including a broken link, no longer receives `write_text`. The outside file stays. A broken link does not create the missing target.
Recover: a regular file still receives the JSON line, and an empty row list writes an empty regular file.

Tests after land: `tests.test_think_proxy_symlink` and `tests.test_hermes_bakeoff`, 35 OK (1 skipped).
