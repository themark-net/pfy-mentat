# 08 make-tasks-symlink

Human: accept.

Why: `main` writes `OUT` through `_write_regular_file`, which `os.replace`s a temp file onto the path. Only `examples/hermes-bakeoff/make_tasks.py` changed (18 insertions, 1 deletion). The `OUT` constant, `build`, and `labels_written_stamp` are untouched. No mkdir was added. The payload is still `json.dumps` with indent 2 plus one trailing newline. The helper cleanup catches `BaseException` so a failed replace still removes the temp file. The gate was red before (exit 1, 2 failures) and 3 tests OK after. Review accepted attempt 1. After land, `tests.test_make_tasks_symlink` and `tests.test_hermes_bakeoff` were 35 OK (1 skipped). The committed tasks file was not rewritten.

Cloud commit: 1ac3db4d3aa386f1a2192369fff7fbfeeacb5048
Landed: a7008f4 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 109
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink at `OUT`, including a broken link, no longer receives `write_text`. The outside file stays. A broken link does not create the missing target.
Recover: a regular `OUT` still receives the task JSON, including schema `hermes-bakeoff.tasks.v0` and `n_tasks` 27.

Tests after land: `tests.test_make_tasks_symlink` and `tests.test_hermes_bakeoff`, 35 OK (1 skipped).
