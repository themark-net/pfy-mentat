# Handoff mvp-cloud347-1031

State: lane empty. Close check 2026-11-01T02:45:36Z. Wall cap 2026-11-01T10:34:05Z is later. MemAvailable about 44 GiB. Load about 3.1 on 32 cores. No host pressure.

Branch `bot/mvp-cloud347-1031`. Base `origin/bot/mvp-probe-int-1031` plus drop-in `79cd260`. No `--local`. No live Grok API. Tests used a fake `--grok-cmd`. `scripts/pregate.sh` was not run.

`Runner.Worker` pid 1511538 was alive at launch, so no python tests ran until it was gone. It was gone by 2026-11-01T02:39:11Z, before the first red run.

## Done

| Item | SHA | What landed |
| --- | --- | --- |
| Exit card before code | `34d7992` | Run log and decisions only. |
| Pass3 finding 3, added lines only | `6f1489e` | `diff_aims_at_root` inspects lines that start with `+` and not `+++`. Deleting `rm -rf /` can land. An added `rm -rf /` or `rm -rf /tmp/x` stays rejected. |
| Run log for finding 3 | `4b1b185` | Docs only. |
| Pass3 finding 4, `.env.*` | `7cb6995` | Basename `.env` or `.env.*` is protected, except `.env.example`. |
| Run log for finding 4 | `22050a5` | Docs only. |
| Pass3 finding 7, reap receipt | `d9a4f44` | A failed ABORTED write exits 1, names the path on stderr, and leaves the pid file so a second `--reap` can write the receipt. |

Checked before the edits: the three bugs were still present on this base. `origin/main` at `c0d38af` has no `diff_aims_at_root`.

## Skipped

- Same-process write through a symlink the agent creates and writes in that turn. Probe-int already refused the commit (`e7703bf`) and left the rollback as an OQ. A sandbox is an isolation design. OQ draft below. Not implemented. Not filed in `docs/OPEN_QUESTIONS.md` because that index is shared.
- Pass3 findings 1 and 2. They are in `scripts/pfy_build_local.py`. This lane does not edit that file.
- Open TODO rows (T-0110, T-0091, and the parked rows). They are not cloud-runner bugs, and `docs/TODO.md` is shared. Dogfood5 already left those rows to other lanes.
- Pregate. This lane's drop-in says the operator runs `scripts/pregate.sh`.

## How each change fails and recovers

Added-line root check (`6f1489e`). A diff that only deletes `rm -rf /` used to be `review-rejected` because the regex scanned removed lines and context lines. Exit was 1 and no branch was kept. Now only added lines count, so removing `danger.sh` and adding `kept.py` can PASS. An added `rm -rf /` is still `review-rejected` when review says accept. An added `rm -rf /tmp/x` stays rejected too. Recovery on that reject is the existing line: "Mark: review rejected the diff. Change the task or the patch, then rerun ./pfy build %s."

Env variants (`7cb6995`). `.env.bak`, `nested/.env.local`, and `nested/.env.production` used to commit. The attempt is now `protected-path-changed`. With a retry, the agent can delete those files and land `.env.example` plus `kept.py`. The strings `bak-secret-value-347`, `local-secret-value-347`, and `prod-secret-value-347` are absent from the receipt. `.env.example` stays committable. A last attempt that still touches a secret env file exits 1. Recovery is the existing protected-path line, which names the path.

Reap receipt (`d9a4f44`). When the dead pid's receipt directory cannot be written, reap used to print `reaped:` and return 0 with no receipt. It now prints `reap: could not write ABORTED receipt <path>: <error>` on stderr and returns 1. `tmp/cloud-build.pids.json` stays. Recovery: make that path a writable directory, then run `./pfy build --reap` again. The second run writes status `ABORTED`, reason `no-receipt`, and exits 0. A live pid still prints `reaped: none` and exits 0. A writable receipt dir still writes `ABORTED` on the first reap and exits 0.

## Test evidence

Targeted, niced, no full discover, no heavy lock. `TMPDIR` was this worktree's `tmp/`.

Red, before each fix:

- `test_removing_a_root_delete_can_land` returned 1, reason `review-rejected`. `test_added_tmp_delete_stays_rejected` already passed.
- `test_env_variants_are_protected_and_example_can_land` had 1 attempt, not 2.
- `test_reap_exits_nonzero_when_the_aborted_receipt_cannot_be_written` returned 0. Stdout was `reaped: reaped <pid>`.

After `d9a4f44`:

`nice -n 19 python3 -m unittest tests.test_pfy_build_cloud`

Ran 71 tests in 22.442s. OK.

The `FAIL:` lines in that run are receipt summaries from `test_every_failure_reason_receipt_has_a_recovery_line`. They are not test failures.

Tests that lock the three findings:

- `test_removing_a_root_delete_can_land`
- `test_added_tmp_delete_stays_rejected`
- `test_root_delete_is_rejected_even_when_review_accepts` (still green)
- `test_env_variants_are_protected_and_example_can_land`
- `test_reap_exits_nonzero_when_the_aborted_receipt_cannot_be_written`

## Cross-lane requests

None. Edits stayed in `scripts/pfy_build_cloud.py`, `tests/test_pfy_build_cloud.py`, and this lane's `docs/ops/` files. `scripts/pfy_build_local.py` and `pfylib/` were not edited.

## Gate

Tester plus Reviewer for the runtime commits `6f1489e`, `7cb6995`, and `d9a4f44`.

This handoff commit is docs only. The docs gate would be pregate plus Reviewer. Pregate was not run.

## Next

Review the three runtime commits. If a same-process write through a new symlink must be stopped, write an ADR for a sandbox first. Do not merge this branch from this lane.

## OQ draft (not in the central index)

Question: Should `./pfy build` sandbox the agent so a write through a symlink created in that same process cannot change a file outside the worktree?

Context: Probe-int's pre-existing-link probe overwrote an outside file and then PASSed. `e7703bf` refuses a link that is already in the tree before grok starts, and refuses a link the agent adds before commit. A link created and written through in one process can still change the outside file before that refusal.

Why this lane did not build it: a sandbox is an isolation design. It needs an ADR and may touch files this lane does not own.

Rejected here: commit the escaping link, or add a sandbox inside `scripts/pfy_build_cloud.py` without an ADR.
