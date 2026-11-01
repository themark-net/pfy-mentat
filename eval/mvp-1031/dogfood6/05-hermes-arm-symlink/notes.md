# 05 hermes-arm-symlink

Human: accept.

Why: `_write_config` writes `config.yaml` through `_write_text`, which `os.replace`s a temp file onto the path. Only `examples/hermes-bakeoff/hermes_arm.py` changed (17 insertions, 1 deletion). No mkdir of home was added. `_redact` and `_extract` are untouched. The gate was red before (exit 1, 2 failures) and 3 tests OK after. Review accepted attempt 1. After land, `tests.test_hermes_arm_symlink` and `tests.test_hermes_bakeoff` were 35 OK (1 skipped).

Cloud commit: 39069ebd86b568cd2c72818c8e8b1ed4e1335071
Landed: 839ae5e (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 95
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at `config.yaml`, including a broken link, no longer receives `write_text`. The outside file stays. A broken link does not create the missing target.
Recover: a regular `config.yaml` still receives the yaml, including the model name and the base URL.

The class scan hit the letters sk- inside the unchanged context word task-id in diff.patch. That is not a credential. The receipt has no key material.

Tests after land: `tests.test_hermes_arm_symlink` and `tests.test_hermes_bakeoff`, 35 OK (1 skipped).
