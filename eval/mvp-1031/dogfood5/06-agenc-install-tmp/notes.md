# 06 agenc-install-tmp

Human: accept.

Why: the Node tarball is `"${TMPDIR:-$NODE_CACHE}/${platform}.tar.xz"`, `mkdir -p "$NODE_CACHE"` stays, and the tarball directory is created before curl. Only `bootstrap/agenc/install.sh` changed. `install_official`, `install_npm`, and `main` are unchanged. Review accepted attempt 1. The gate was red before the edit and 2 tests OK after.

Cloud commit: bc672303791a7b5d3e45f1bfe009c38ded53c258
Landed: 4828050 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 116
Attempts: 1
Review: accept
Exit: 0

Attempt 1 of this item was a human reject. Cloud `4def314` deleted `mkdir -p "$NODE_CACHE"`. That receipt is `../06-agenc-install-reject/`. This run keeps the extract directory.

Fail: an old node chooses a tarball under TMPDIR, curl is fail-closed (the test curl exits 1), and NODE_CACHE still exists for the extract. Nothing is written under `/tmp`.
Recover: a node at major 25 or newer returns before any tarball path is chosen, so no `/tmp` tarball is requested. Unset TMPDIR uses NODE_CACHE for the tarball.

Tests after land: `tests.test_agenc_install_tmpdir`, 2 OK.
