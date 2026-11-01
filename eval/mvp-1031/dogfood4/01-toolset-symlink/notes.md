# 01 toolset-symlink

Human: accept.

Why: only `pfylib/toolsets.py` changed. `_put_text` uses `os.replace`, so an in-root symlink becomes a regular file. `_regular_text` and the json-merge branch do not read a symlink. `_under`, `_apply_symlink`, and symlink mode are unchanged. The gate was red (3 failures) before the edit and 5 OK after. Review accepted attempt 1. One em dash in the receipt attempt tail was replaced with " - " before this commit. Status fields were not changed.

Cloud commit: 5d542ce232b881a271a8052c14f183e8418cc278
Landed: d900cc3 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 126
Attempts: 1
Review: accept
Exit: 0

Fail: write, append-marker, and json-merge on a symlink inside an allowed root replace the symlink and leave the target bytes as they were.
Recover: a regular file still updates in place. A symlink that resolves outside the allowed roots stays refused, and the outside bytes stay.

Tests after land: `tests.test_toolset_apply_symlink` and `tests.test_toolsets`, 29 OK.
