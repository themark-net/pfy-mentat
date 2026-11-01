# 04 smoke137-timeout

Human: accept.

Why: `timeout_problem` is imported from `smoke_140_142` and is not copied. `main` returns 2 before the entry. Unset or empty still reports the neatroots prereq miss. Only `examples/x-intake-local/smoke_137_139.py` changed. `tree_hash` is untouched. The worktree gate was red before the edit and green after. Review accepted attempt 1.

Cloud commit: cc05a173ea0bee987de4f519e602a29cc0cbd4ee
Landed: d75d407865efcda24be06e1b895fae8950b74faf (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 95
Attempts: 1
Review: accept
Exit: 0

Attempt 1 of this item failed `commit-recheck-failed` because the planted test required `tmp/` on a fresh extract. That receipt is `../04-smoke137-recheck-fail/`. This run used the test that creates `tmp/` first.

Fail: a set PFY_XINTAKE_TIMEOUT that is not a finite number of seconds > 0 exits 2 and the reason names the variable. The entry does not run.
Recover: unset or empty still calls the entry, so a missing neatroots app reports `neatroots not found ($NEATROOTS_APP or tmp/neatroots/app with neatroots/dist/cli.js); unpack the v0.2.9 neatroots.tar.gz there, see the handoff. Never run install.sh`.

Tests after land: `tests.test_smoke_137_bad_timeout` and `tests.test_x_intake_smoke_137_139`, 57 OK.
