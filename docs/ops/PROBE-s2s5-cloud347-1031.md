# Probe: S2-S5 and cloud347 (2026-10-31)

Lane `bot/mvp-probe-s2s5-1031`. Branch A pin `493935b` (`origin/bot/mvp3-s2s5-1031`, already in this worktree). Branch B pin `9d75395` (`origin/bot/mvp-cloud347-1031`), read from a `git archive` under `tmp/cloud347-src`. No second git worktree. No `--local` model. No pregate.

CLI drivers (not committed): `tmp/probes/probe_a.py` through `./pfy build --local`, and `tmp/probes-b/run_probes.py` through `python3 scripts/pfy_build_cloud.py` with a fake `--grok-cmd`. `TMPDIR` was this worktree's `tmp/scratch` and `tmp/scratch-b`. `nice -n 19`. No process with comm `Runner.Worker` was present. `pgrep -f` also matched flock scripts that quote that name. Those were not the runner.

Counts: 48 probes. Branch A: 21 holds, 1 defect, 1 residual. Branch B: 20 holds, 5 notes, 0 defects.

The one defect is fixed on this branch in `abc8985`.

## Branch A

Contract under test: S2 wall budget ends TIMEOUT `wall-timeout` exit 3. S3 labels a non-zero empty diff `agent-crashed` and still gates a non-zero exit that wrote files. S4 spent rejection is FAIL `review-rejected`, summary starts with `FAIL`, no `PASS-REJECTED`. S5 `--reap` and the next run remove only a recorded `tmp/local-build-*` path and leave every other worktree.

| Probe | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| A2-env | env `PFY_LOCAL_BUILD_WALL_TIMEOUT=2`, sleep 30, no flag: exit 3, `wall-timeout`, under 3 attempts, under 12s, no commit | exit 3, TIMEOUT `wall-timeout`, attempts 1, 2.185s, commit null | holds |
| A2-flag-beats-env | `--wall-timeout 30` beats env 2. Not `wall-timeout` | exit 1, FAIL `no-change`, 1.331s, not wall-timeout | holds |
| A2-agent-timeout-not-wall | `--timeout 1 --wall-timeout 30`, sleep 30: TIMEOUT `timeout`, attempts 1, no retry | exit 3, TIMEOUT `timeout`, attempts 1, 1.275s, no commit | holds |
| A2-crash-then-wall | crash then sleep 30, wall 3s: final `wall-timeout`, attempt 1 `agent-crashed`, under 15s | exit 3, TIMEOUT `wall-timeout`, attempts 2, attempt 1 FAIL `agent-crashed`, 3.169s, no commit | holds |
| A2-zero | `--wall-timeout 0` is usage exit 2, no PASS receipt | exit 2, no receipt, stderr says wall-timeout must be positive | holds |
| A2-negative | `--wall-timeout -1` exit 2 | exit 2, no receipt | holds |
| A2-foo | `--wall-timeout foo` exit 2 | exit 2, argparse invalid float, no receipt | holds |
| A2-review-block | wall 2s while review HTTP is held: TIMEOUT `wall-timeout`, process exits itself | exit 3, TIMEOUT `wall-timeout`, attempts 1, 2.142s, review had started, no forced kill, no commit | holds |
| A3-exit0-empty | exit 0 and no writes: FAIL `no-change`, not `agent-crashed` | exit 1, FAIL `no-change`, files empty, no commit | holds |
| A3-write-then-nonzero | write the real calc fix then `os._exit(70)`: not `agent-crashed` | exit 0, PASS `ok`, files `src/calc.py`, commit set | holds |
| A3-partial | write a broken calc then `os._exit(70)`: gate sees the file | exit 1, FAIL `tests-failed`, files `src/calc.py`, no commit | holds |
| A3-ignored-only | write only `tmp/note.txt` then exit 70: empty diff is `agent-crashed` | exit 1, FAIL `agent-crashed`, files empty, no commit | holds |
| A4-size | over `--max-lines 5` with an accepting review: FAIL `review-rejected`, summary starts `FAIL`, no commit | exit 1, FAIL `review-rejected`, attempt status FAIL, summary `FAIL review-rejected`, no `PASS-REJECTED`, no commit | holds |
| A4-intermediate | out-of-scope then a good fix: attempt 1 FAIL, final PASS | exit 0, PASS, attempts 2, attempt 1 FAIL `review-rejected`, commit set | holds |
| A4-no-review-large | same large diff with `--no-review`: not `review-rejected` | exit 0, PASS `ok`, attempts 1, commit set | holds |
| A4-symlink | `src/calc.py` symlinked at an outside sentinel: FAIL in the operator status set, sentinel bytes unchanged | exit 1, FAIL `review-rejected`, no commit, outside bytes unchanged | holds |
| A5-reap-only | SIGKILL after the pid file, then `--reap`: killed path gone, sibling `local-build-keep-sibling` stays | exit 0, killed path gone from disk and `git worktree list`, sibling listed, sentinel `keep` | holds |
| A5-outside-symlink | replace the recorded path with a symlink to an outside dir, then `--reap`: outside `KEEP` stays | exit 0, no prune of the outside path, sentinel still `OUTSIDE-KEEP` | holds |
| A5-sibling-symlink | replace the recorded path with a symlink to sibling `local-build-keep-sibling`, then `--reap`: sibling stays | exit 0, stdout `pruned local-build-keep-sibling`, sibling and sentinel gone, worktree list was only the temp repo root | defect |
| A5-plain-prefix | `tmp/not-a-build` stays. Plain dir `tmp/local-build-orphan` is removed | first reap kept `not-a-build`. Second reap stdout `pruned local-build-orphan`, orphan gone, plain sentinel still present | holds |
| A5-truncated-pid | pid file is `{`: do not delete the registered worktree, do not crash | exit 0, `reaped: none`, no traceback, worktree still listed | holds |
| A5-odd-name | pid names `tmp/local-build-odd name`: only that directory goes | exit 0, `pruned local-build-odd name`, neighbor sentinel `neighbor-keep` stayed | holds |
| A5-early-kill | SIGKILL after the worktree exists and before the pid file: leftover is a note | one `local-build-*` stayed on disk and in `git worktree list`. `--reap` printed `reaped: none` | residual |

### A5 defect, fixed in abc8985

`_recorded_build_worktree` used `Path.resolve()`, which follows the leaf. A `local-build-*` symlink whose target is another `local-build-*` directory under `<repo>/tmp` was treated as that target. `--reap` then ran `git worktree remove` and `rmtree` on the sibling.

Red, before the fix: `test_reap_does_not_follow_a_symlink_onto_a_sibling_worktree` failed because stdout contained `pruned local-build-keep-sibling`.

After `abc8985`: the leaf is not resolved. A symlink is unlinked and not followed. The same test keeps the sibling sentinel `SIBLING-KEEP` and an outside sentinel `OUTSIDE-KEEP`. A real directory named `local-build-*` directly under `tmp` is still removed (A5-reap-only and A5-odd-name, and `test_sigkill_worktree_is_pruned_on_the_next_run`).

How it fails: the pid file names `tmp/local-build-<stamp>`, and that path has been replaced with a symlink. How it recovers: `./pfy build --local --reap`, or the next `./pfy build --local`, unlinks only that name. The target stays. Run `--reap` again after the name is gone. It does not walk every `local-build-*` directory, so a sibling that was never the recorded path stays.

### Residual, not fixed

A5-early-kill: SIGKILL in the window after `git worktree add` and before the pid file write leaves an unrecorded worktree. The handoff for S5 says the pid file is the handle. Pruning every `local-build-*` name would also delete the sibling A5-reap-only is required to keep. Recovery for that window is `git worktree remove --force` on the leftover path.

## Branch B

Contract under test: `diff_aims_at_root` counts lines that start with `+` and not `+++`. Deleting `rm -rf /` can land. An added `rm -rf /` or `rm -rf /tmp/x` stays `review-rejected`. Basename `.env` or `.env.*` is protected, except `.env.example`. A failed ABORTED receipt write exits 1, names the path, and leaves the pid file so a second `--reap` can write it.

No product file on this branch was edited for these probes. `scripts/pfy_build_cloud.py` was not touched.

| Probe | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| B1-delete-only | delete `danger.sh` (`rm -rf /`) and add `kept.py`: PASS | exit 0, PASS, `danger.sh` gone, `kept.py` is `value = 1`, caller HEAD unchanged | holds |
| B1-add-root | added `rm -rf /`: `review-rejected`, no branch | exit 1, FAIL `review-rejected`, added line `+rm -rf /`, no cloud branch | holds |
| B1-add-tmp | added `rm -rf /tmp/x`: rejected | exit 1, `review-rejected`, added line `+rm -rf /tmp/x`, no branch | holds |
| B1-context | danger only on a context line (` rm -rf /`): not a root reject | exit 0, PASS, added hits empty, context hit is the spaced line | holds |
| B1-plus-header | `+++` header contains `rm -rf /`: header alone does not reject | exit 0, PASS, header `+++ b/rm -rf /kept.py`, added line `+value = 1` | holds |
| B1-both | delete `rm -rf /` and add `rm -rf /tmp/x`: rejected | exit 1, `review-rejected`, added `+rm -rf /tmp/x`, removed `-rm -rf /` | holds |
| B1-tab | added `rm` tab `-rf` tab `/`: rejected | exit 1, `review-rejected`, added line has those tabs | holds |
| B1-comment | added `# do not rm -rf /`: record it. The handoff did not promise comments can land | exit 1, `review-rejected`. The regex is unanchored, so the comment matches | note |
| B1-flags | added `rm -rf -- /` and `rm -r -f /`: record it. The handoff names `rm -rf /` and `rm -rf /tmp/x` | exit 0, PASS, both lines landed. Neither matches `rm\s+-rf\s+/` or `rm\s+-fr\s+/` | note |
| B1-case | added `RM -RF /`: rejected (regex is case insensitive) | exit 1, `review-rejected` | holds |
| B2-example-ok | `.env.example` plus `kept.py` can land | exit 0, PASS, blob `EXAMPLE=1` | holds |
| B2-bak | `.env.bak` with `bak-secret-value-347`: `protected-path-changed`, marker absent from the receipt | exit 1, `protected-path-changed`, marker absent, no branch | holds |
| B2-nested | `nested/.env.local` and `nested/.env.production`: protected, markers absent | exit 1, `protected-path-changed`, stderr names both paths, markers absent | holds |
| B2-example-bak | `.env.example.bak` is not the exception | exit 1, `protected-path-changed`, not committed | holds |
| B2-dot-env-dot | basename `.env.` is protected | exit 1, `protected-path-changed`, not committed | holds |
| B2-case | `.ENV` and `.Env.local`: defect only if the code claims case-insensitive protection | both PASS. The check is `name == ".env" or name.startswith(".env.")` with no casefold | note |
| B2-symlink-name | `.env.example` as a symlink: do not PASS after changing an outside sentinel | (1) link to outside: exit 1 `symlink-escape`, sentinel unchanged. (2) write through the link: exit 1 `symlink-escape`, sentinel changed, not PASS. (3) link to in-tree `.env`: PASS, mode 120000, blob text `.env`, secret marker absent from the receipt | note |
| B2-both | `.env.example` and `.env.local` together, then a retry that drops `.env.local`: second attempt can land, `.env.local` not in the commit | exit 0, PASS, attempt 1 `protected-path-changed`, attempt 2 PASS, commit names `.env.example` and `kept.py` only | holds |
| B3-file-parent | receipt parent is a file: exit 1, stderr names the path, pid file stays | exit 1, stderr `reap: could not write ABORTED receipt ... Errno 20 Not a directory`, pid file present | holds |
| B3-retry | make that path a directory and `--reap` again: exit 0, ABORTED `no-receipt`, pid file removed | exit 0, receipt ABORTED `no-receipt`, pid file removed | holds |
| B3-live | live pid: `reaped: none`, exit 0, do not kill the child | exit 0, `reaped: none`, `sleep 180` still alive, then this probe killed its own child | holds |
| B3-symlink-escape | receipt dir is a symlink to a scratch dir with `sentinel.txt`: do not destroy the sentinel | exit 0, ABORTED `receipt.json` written through the symlink, sentinel bytes unchanged | note |
| B3-partial-json | pid file is `{`: no traceback, innocent dir stays | exit 0, `reaped: none`, no traceback, `keep-me` still present, corrupt pid file removed | holds |
| B3-already-there | existing PASS receipt is not overwritten with ABORTED | exit 0, receipt bytes unchanged, status stayed PASS | holds |
| B3-odd-name | receipt dir `odd name 347`: the receipt lands on that name | exit 0, receipt at `odd name 347/receipt.json`, stdout `aborted odd name 347` | holds |

### Notes, not defects

These do not break the contract stated in `docs/ops/HANDOFF-mvp-cloud347-1031.md`. They are not cross-lane fix requests.

- B1-comment: an added comment that mentions `rm -rf /` is rejected. The regex searches the whole added line. Loosening it was not this probe's job.
- B1-flags: `rm -rf -- /` and `rm -r -f /` land when review accepts. The handoff requires `rm -rf /` and `rm -rf /tmp/x`, which still reject. Widening the regex is a product choice, not a break of `6f1489e`.
- B2-case: `.ENV` and `.Env.local` commit. The check is case-sensitive and does not claim otherwise.
- B2-symlink-name: a write through a symlink created in the same turn can change an outside file before the run exits 1 `symlink-escape`. It does not PASS. The cloud handoff already parked a sandbox for that as an OQ. An in-tree link named `.env.example` commits as the link text, not the secret bytes.
- B3-symlink-escape: reap writes the ABORTED receipt at the recorded path, which followed a symlink. The sentinel file was not overwritten.

## Commands

- `nice -n 19 timeout 420 python3 tmp/probes/probe_a.py a2` then `a2rest`, `a3`, `a4`, `a5`
- `nice -n 19 python3 -u tmp/probes-b/run_probes.py` (8.245s)
- Red: `nice -n 19 python3 -m unittest tests.test_pfy_build_local.LocalBuildTests.test_reap_does_not_follow_a_symlink_onto_a_sibling_worktree` (FAIL on `pruned local-build-keep-sibling`)
- Green modules, before the outside-link lines were added to that test: `nice -n 19 python3 -m unittest tests.test_pfy_build_local tests.test_pfy_build_local_review` (104 OK in 173.921s)
- Green again after the outside-link lines: the same one test, 1 OK in 0.630s
