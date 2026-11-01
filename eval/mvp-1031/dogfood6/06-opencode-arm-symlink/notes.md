# 06 opencode-arm-symlink

Human: accept.

Why: `_write_config` writes `opencode.json` through `_write_text`, which `os.replace`s a temp file onto the path. Only `examples/hermes-bakeoff/opencode_arm.py` changed (17 insertions, 1 deletion). Both mkdir calls stay. `_parse_events` and `main` are untouched. The gate was red before (exit 1, 2 failures) and 3 tests OK after. Review accepted attempt 1. After land, `tests.test_opencode_arm_symlink` and `tests.test_hermes_bakeoff` were 35 OK (1 skipped).

Cloud commit: 1f469327c8a1866442365966d1c3aa73b83af51c
Landed: 51ed297 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 99
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at `opencode.json`, including a broken link, no longer receives `write_text`. The outside file stays. A broken link does not create the missing target.
Recover: a regular `opencode.json` still receives the JSON, including model `ollama/<model>` and the provider baseURL.

Tests after land: `tests.test_opencode_arm_symlink` and `tests.test_hermes_bakeoff`, 35 OK (1 skipped).
