# 08 files-under-symlink

Human: accept.

Why: only `files_under` in `examples/x-intake-local/smoke_143_145.py` changed. A symlink is skipped and not opened. A regular file is still listed. `site_digest` was not edited. The gate was red (1 failure) before the edit and 1 OK after. Review accepted attempt 1. This was the 8th cloud build, so the turn cap stops the lane here.

Cloud commit: a2123f737de3ad0ff533017885bc35b5b9edb859
Landed: b74d5c9 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 55
Attempts: 1
Review: accept
Exit: 0

Fail: a symlink inside the directory is omitted from the name list, and the target bytes stay.
Recover: a regular file in the same directory is still listed. The taste-skill suite still passes.

Tests after land: `tests.test_smoke_143_files_under`, `tests.test_smoke_143_site_digest`, and `tests.test_x_intake_smoke_143_145`, 74 OK (1 skipped).
