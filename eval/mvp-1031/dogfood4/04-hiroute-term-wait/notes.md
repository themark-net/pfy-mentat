# 04 hiroute-term-wait

Human: accept.

Why: only `examples/x-intake-local/smoke_146_147.py` changed. `term_wait_problem` strips the value, treats whitespace-only as unset, and fail-closes when the number is not finite or not in (0, 600]. `main` calls it only for the hiroute entry, after `timeout_problem` and before the entry. `term_wait()` is unchanged. The gate was red (6 failures) before the edit and 3 OK after. Review accepted attempt 1.

Cloud commit: 8a46224d1a3fd2fede820e212abc8aa028d60727
Landed: d507591 (Built-by trailer added; author stays pfy-cloud-build)
Wall seconds: 68
Attempts: 1
Review: accept
Exit: 0

Fail: abc, 0, -1, nan, inf, and 601 exit 2 with a reason that names HIROUTE_TERM_WAIT and does not say the archive is not staged.
Recover: unset, empty, whitespace-only, 10, 600, and a padded 10 still reach the staging miss. skill-up with HIROUTE_TERM_WAIT=abc still reports skill-up not found.

Tests after land: `tests.test_smoke_146_term_wait` 3 OK, and `tests.test_x_intake_smoke_146_147` 35 OK.
