# Handoff: mvp-probe-s2s5-1031

Lane: adversarial probes of S2-S5 and of cloud347, then fix real defects on branch A.
Branch: `bot/mvp-probe-s2s5-1031`. Worktree: `~/DEVELOP/pfy-mentat/tmp/mvp-probe-s2s5-1031`.
Base: `origin/bot/mvp3-s2s5-1031` at `493935b`. Cloud pin read only: `origin/bot/mvp-cloud347-1031` at `9d75395`.
Exit: lane empty. Launch 2026-11-01T02:52:01Z. Wall cap 2026-11-01T10:52:01Z. Clock at exit: 2026-11-01T03:21:20Z.
MemAvailable about 50 GiB. Load about 3.0 on 32 cores. No host pressure. No `Runner.Worker` comm. Pregate not run.

No merge, no PR, no tag. `scripts/pfy_build_cloud.py` was not edited. No local model.

## Done

| Item | SHA | What landed |
| --- | --- | --- |
| Exit card | `7c21b6d` | Run log and decisions before probes |
| Doc sentence | `0388e97` | `docs/ops/HANDOFF-pfy-local-build-mvp.md`: a larger diff is FAIL reason `review-rejected`, summary starts with `FAIL` |
| Doc sentence sha | `1bd60f5` | Run log names `0388e97` |
| Probe A | scratch only | 23 CLI probes of S2-S5. 21 holds, 1 defect, 1 residual |
| Probe B | scratch only | 25 CLI probes of the three cloud347 fixes. 20 holds, 5 notes, 0 defects |
| S5 symlink | `abc8985` | `--reap` unlinks a recorded `local-build-*` symlink and does not follow it |
| Probe report | this handoff's commit | `docs/ops/PROBE-s2s5-cloud347-1031.md` |

## Skipped

- A5-early-kill. SIGKILL after `git worktree add` and before the pid file leaves an unrecorded worktree. The S5 contract says the pid file is the handle. Deleting every `local-build-*` name would also remove the sibling the contract keeps. Recovery: `git worktree remove --force` on that leftover path.
- Branch B notes (comment line, `rm -rf -- /`, case-sensitive `.ENV`, same-process symlink write, reap write through a receipt symlink). They do not break the cloud347 handoff contract. Not filed as cross-lane fixes. The same-process symlink write is already an OQ draft on `docs/ops/HANDOFF-mvp-cloud347-1031.md`.
- Open TODO rows and `eval/mvp3/run_trial.py`. Not this lane. The eval scorer still accepts an old `PASS-REJECTED` receipt on purpose.
- Pregate. The drop-in says the operator runs `scripts/pregate.sh`.
- No item needed special hardware, a secret, or a new ADR.

## How the code change fails and recovers

S5 symlink (`abc8985`). The pid file names `<repo>/tmp/local-build-<stamp>`. If that path is a symlink to another `local-build-*` worktree, the old code resolved the link and `--reap` deleted the sibling (`pruned local-build-keep-sibling`, sentinel gone). It now unlinks only the recorded name. The sibling and an outside target stay. A real directory (not a symlink) directly under `tmp` whose name starts with `local-build-` is still removed. Recovery: run `./pfy build --local --reap` or the next `./pfy build --local`. A second reap after the name is gone does not walk other worktrees.

The doc sentence is docs only. Nothing fails at runtime. Readers of the operator handoff now see FAIL `review-rejected` for a diff over the size cap.

## Test evidence

Targeted, niced, `TMPDIR` under this worktree's `tmp/scratch`. No full discover. No heavy lock. No local model.

Red, before `abc8985`:

`nice -n 19 python3 -m unittest tests.test_pfy_build_local.LocalBuildTests.test_reap_does_not_follow_a_symlink_onto_a_sibling_worktree`

FAIL in 0.625s. stdout was `reaped: reaped <pid>, aborted hang-1, pruned local-build-keep-sibling`.

After the fix, before the outside-link lines were added to that test:

`nice -n 19 python3 -m unittest tests.test_pfy_build_local tests.test_pfy_build_local_review`

Ran 104 tests in 173.921s. OK.

BrokenPipeError and ResourceWarning lines showed up. The run still exited 0. Those lines were already noted on the S2-S5 handoff.

After the outside-link assertions were added to the same test:

that one test, 1 OK in 0.630s. Sibling sentinel `SIBLING-KEEP` and outside sentinel `OUTSIDE-KEEP` both stayed.

Probe batches (scratch, not the product suite):

- `tmp/probes/probe_a.py` batches a2, a2rest, a3, a4, a5. 21 holds, 1 defect, 1 residual.
- `tmp/probes-b/run_probes.py`. 25 probes, 8.245s, 20 holds, 5 notes, 0 defects.

## Cross-lane requests

None. Branch B produced no contract defect. Notes are in the probe doc so the cloud lane can read them. This lane did not edit `scripts/pfy_build_cloud.py`.

## Gate

Runtime: `abc8985` (`scripts/pfy_build_local.py` and `tests/test_pfy_build_local.py`). Gate: Tester plus Reviewer.

Docs: `7c21b6d`, `0388e97`, `1bd60f5`, and this handoff commit. Gate: pregate plus Reviewer. Pregate was not run.

## Next step

Hand `bot/mvp-probe-s2s5-1031` to Tester and Reviewer for `abc8985`. Read `docs/ops/PROBE-s2s5-cloud347-1031.md` with that review. Do not merge from this lane. Do not widen the cloud root regex from the B1-flags note unless a later lane decides that those flag forms are in contract.
