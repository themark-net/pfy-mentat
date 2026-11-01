# 05 agenc-smoke-tmp

Human: accept.

Why: the optional LLM tee uses `"${TMPDIR:-${ROOT}/tmp}/agenc-smoke-llm.txt"`, and the failure text names that path. Only `bootstrap/agenc/smoke.sh` changed. The other checks and the results line are unchanged. The gate was red before the edit and 2 tests OK after. Review accepted attempt 1.

Cloud commit: 01115aaf1c096ee155369b349081ebd003a7ab62
Landed: ef1f2c2 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 118
Attempts: 1
Review: accept
Exit: 0

Fail: with `AGENC_SMOKE_LLM=1`, a non-PONG answer exits 1 and the message names the log under TMPDIR. The run does not create `/tmp/agenc-smoke-llm.txt`.
Recover: a PONG answer exits 0 and the log file is under TMPDIR. Unset TMPDIR falls back to `${ROOT}/tmp`, not `/tmp`.

Tests after land: `tests.test_agenc_smoke_tmpdir`, 2 OK.
