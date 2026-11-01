# Handoff mvp-probe-int-1031

State: lane empty. Close check 2026-11-01T01:57:13Z. Wall cap 2026-11-01T09:33:31Z is later. MemAvailable about 56 GiB. Load about 3.5 on 32 cores. No host pressure.

Branch `bot/mvp-probe-int-1031`. Base `origin/bot/mvp-integrate-1031` at `1dee0b9`, plus drop-in `2742345`. Probes called `./pfy build` with a fake `--grok-cmd`. No `--local`. No live Grok API. Scratch stayed under this worktree's `tmp/probe-int/`.

## Probe table

Observed rows are the first scratch pass, before the fixes. The After column is what the behavior tests lock.

| Probe | Expected fail-closed | Observed receipt | Score | After |
| --- | --- | --- | --- | --- |
| Dirty worktree | Caller porcelain stays dirty. Those paths are not in the new commit. Caller HEAD unchanged. A valid agent edit may PASS. | Exit 0, reason `ok`. Porcelain before and after: ` M README.md` and `?? caller-dirty.txt`. Commit names `kept.py`. README in the commit is `fixture`. `caller-dirty.txt` is not in the tree. HEAD unchanged. | PASS | No code change. |
| Detached HEAD, sha is not `origin/main` | Exit 2 before grok. Caller stays detached. No `cloud/` branch. | Exit 2. No receipt (usage before `CloudBuild`). Stderr: HEAD `0d30b452da3c` is not origin/main `8755fad4f7a0`, pass `--base`. `grok_started` false. Still detached. No new branch. | PASS | No code change. A usage exit 2 has no receipt. |
| Detached HEAD, sha matches `origin/main` | Build that sha. Caller stays detached at the same sha. | Exit 0, reason `ok`. Still detached. `kept.py` in the commit. HEAD unchanged. | PASS | No code change. |
| Detached HEAD, no `origin/main` | Build HEAD. Caller stays detached at the same sha. | Exit 0, reason `ok`. Still detached. HEAD unchanged. | PASS | No code change. |
| Shell metacharacters in the task | The task is data. No side file is created. The receipt stores the task text. A valid agent edit may PASS. | Exit 0, reason `ok`. Stored task matches, including `touch` of `PWNED`, `$(id)`, a pipe to `tee`, and a backtick `touch`. `pwned_exists` false. `kept.py` committed. | PASS | No code change. |
| Unicode paths | The commit names the path the agent creates, or the run fails with no branch and the caller unchanged. | Exit 0, reason `ok`. Commit names `café/笔记.txt` (bytes `unicode-ok`) and `ok-✅.txt`. HEAD unchanged. | PASS | No code change. |
| Symlink already outside the worktree | An outside target is not modified. Do not run the agent through the link. | Exit 0, reason `ok`. Outside file changed from `SECRET` to `OVERWRITTEN`. Commit contains `leak` mode 120000. | FINDING | `e7703bf`. Exit 1, reason `symlink-escape`. Grok does not start. Outside bytes stay put. |
| Symlink the agent creates outside the worktree | A new commit does not add a symlink whose target resolves outside the worktree. | Exit 0, reason `ok`. Commit contains `leak` mode 120000. Outside file stayed `SECRET` (that probe did not write through the new link). | FINDING | `e7703bf`. Exit 1, reason `symlink-escape`, before commit. The link is not in the tree. |
| Gate rewrites a file | Committed bytes are not the gate rewrite. If the gate changes the tree, no branch. | Exit 0, reason `ok`. Agent wrote `value = 1`. Commit `kept.py` is `value = 999`. | FINDING | `30b3c3a`. Exit 1, reason `gate-rewrote`. No branch. |
| Hung gate | Exit 3, reason `timeout`, no branch, child gone, returns without the outer wait. | Exit 3, reason `timeout`, receipt exit 3, no branch, elapsed 4.088s. Recovery names the gate timeout and a longer `--timeout`. | PASS | No code change. |
| Review reject, then retry | Exit 0, one branch, commit is the accepted attempt only. | Exit 0, reason `ok`. One cloud branch. `kept.py` is `value = 1`. `bad.py` absent. | PASS | No code change. |
| Network loss (closed port) | Does not hang, does not PASS, partial file is not committed, caller unchanged. Other non-zero grok text that is not network, rate-limit, or auth may still run the gate. | Exit 0, reason `ok`, in 0.176s. Port 1 closed. `partial.py` is in the commit. | FINDING | `9028d4f`. Exit 1, reason `network`. Gate does not run. A non-zero grok exit whose text is `boom` can still PASS. |
| SIGTERM mid-agent | Exit 1, reason `interrupted`, no branch. Signal only this run's child. | Exit 1, reason `interrupted`, no branch. `signaled` true. Fake grok was ready and is not still alive. HEAD unchanged. | PASS | No code change. |
| Two builds at once | Caller unchanged. No cross-contaminated commit. A single pid slot must not drop a live build. Second start is busy. | Both exit 0. Commit A has only `alpha.py`. Commit B has only `beta.py`. Caller HEAD and porcelain unchanged. Mid-run pid file named one pid (`1096200`) while both agents were ready. | FINDING | `e2da1d6`. Second start exits 1, reason `build-busy`, and does not start grok. Finish removes the pid file only when the pid is this process. The first build can still PASS. |

## Done

| Item | SHA | What landed |
| --- | --- | --- |
| Exit card before probes | `f5416b8` | Run log and decisions only. |
| Symlink out of scope | `e7703bf` | Reason `symlink-escape`. Pre-existing link stops before grok. Agent-created link is refused before commit and is not retried. |
| Gate rewrites the tree | `30b3c3a` | Reason `gate-rewrote`. Manifest compared after each completed gate. Timeout and interrupt still win when the gate does not return. |
| Closed endpoint | `9028d4f` | Reason `network` on a non-zero grok exit whose text matches a closed-endpoint phrase. Checked on implement and on review. |
| Second build | `e2da1d6` | Reason `build-busy` on `tmp/cloud-build.lock`. Pid file unlink is pid-checked. Unwritable `tmp/` at lock time stays `worktree-failed`. |

## Skipped

- Same-process write through a symlink the agent creates and writes in that turn. The refusal stops the commit. It does not roll back a write that already happened. A sandbox is an isolation design, so it is an OQ draft below and was not implemented. It was not filed in `docs/OPEN_QUESTIONS.md` because that index is shared across lanes.
- Further MVP work outside this lane (mutation harness, dogfood friction, local review, catalog). Those files belong to other lanes.
- Pregate not run: this lane forbids `scripts/pregate.sh`. `Runner.Worker` was also present (pid 1225684), so the shared-host idle check would have skipped it too.

## How each change fails and recovers

Symlink escape (`e7703bf`). A link whose target leaves the worktree fails closed. Exit 1. No branch. Recovery: "Mark: a symlink points outside the worktree (%s). Remove it and rerun ./pfy build %s. The build did not commit that link." A write the agent already made through a link in the same process is not rolled back.

Gate rewrote (`30b3c3a`). A completed gate that changes the worktree manifest fails closed. Exit 1. No retry. No branch. Recovery: "Mark: the gate rewrote the worktree. The branch was not kept. Fix the gate so it only checks, then rerun ./pfy build %s." A gate that sleeps until timeout stays reason `timeout`, exit 3.

Network (`9028d4f`). A non-zero grok exit whose text says the endpoint could not be reached fails closed. Exit 1. The gate does not run. Recovery: "Mark: the cloud endpoint could not be reached. Check the network, then rerun ./pfy build %s." Phrases: connection refused, connection reset by peer, failed to establish a new connection, name or service not known, network down, network is unreachable, network unreachable, no route to host, temporary failure in name resolution. Other non-zero text still runs the gate.

Build busy (`e2da1d6`). A second `./pfy build` while `tmp/cloud-build.lock` is held fails closed. Exit 1. Grok does not start. Recovery: "Mark: another cloud build is already running on this repo. Wait for it to finish, then rerun ./pfy build %s." `--dry-run` and `--reap` do not take the lock. Finish unlinks `cloud-build.pids.json` only when the recorded pid is this process.

## Test evidence

2026-11-01T01:58Z, tree at `e2da1d6`, before this handoff commit:

`nice -n 19 python3 -m unittest tests.test_pfy_build_cloud`

Ran 67 tests in 21.784s. OK.

The `FAIL:` lines in that run are receipt summaries from `test_every_failure_reason_receipt_has_a_recovery_line`. They are not test failures.

Tests that lock the four findings:

- `test_preexisting_symlink_outside_the_worktree_does_not_run_grok`
- `test_agent_symlink_outside_the_worktree_is_not_committed`
- `test_gate_rewrite_is_not_committed`
- `test_closed_port_does_not_commit_the_partial_edit`
- `test_other_nonzero_grok_still_runs_the_gate_and_can_pass`
- `test_second_build_is_busy_and_leaves_the_live_pid`

`test_hung_gate_is_timeout_and_does_not_commit` and `test_unwritable_tmp_is_worktree_failed_and_does_not_call_grok` stayed green next to the new reasons.

## Cross-lane requests

None. Edits stayed in `scripts/pfy_build_cloud.py`, `tests/test_pfy_build_cloud.py`, and this lane's `docs/ops/` files. `scripts/pfy_build_local.py` and `pfylib/` were not edited.

## Gate

Tester plus Reviewer for the runtime commits `e7703bf`, `30b3c3a`, `9028d4f`, and `e2da1d6`.

This handoff commit is docs only. The docs gate would be pregate plus Reviewer. Pregate was not run.

## Next

Review the four runtime commits. If a same-process write through a new symlink must be stopped, write an ADR for a sandbox first. Do not merge this branch from this lane.

## OQ draft (not in the central index)

Question: Should `./pfy build` sandbox the agent so a write through a symlink created in that same process cannot change a file outside the worktree?

Context: The pre-existing-link probe overwrote an outside file and then PASSed. The fix refuses a link that is already in the tree before grok starts, and refuses a link the agent adds before commit. A link created and written through in one process can still change the outside file before that refusal.

Why this lane did not build it: a sandbox is an isolation design. It needs an ADR and may touch files this lane does not own.

Rejected here: commit the escaping link, or add a sandbox inside `scripts/pfy_build_cloud.py` without an ADR.
