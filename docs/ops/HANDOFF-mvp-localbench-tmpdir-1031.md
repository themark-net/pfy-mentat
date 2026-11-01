# Handoff: mvp-localbench-tmpdir-1031

Branch: `bot/mvp-localbench-tmpdir-1031`
Head: `4ff2c67` plus the handoff commit that adds this file.
Base: `origin/bot/mvp-integrate-1031`
Exit: lane empty. Not a Feature GO. No merge, no PR.

## Done

| Item | SHA | Result |
|------|-----|--------|
| Absolute bench log path, plus a test that runs TMPDIR inside the repo and outside it | `4ff2c67` | `tests.test_local_bench` 18 OK both ways |
| Grep `tests/` for `tempfile.gettempdir()` and `/tmp` | none | Not the same bug. No edit. |
| Full discover under the heavy lock with `TMPDIR=$PWD/tmp` | `4ff2c67` (code) | Ran 1244 tests in 895.776s, OK (skipped=16), EXIT 0 |

## Skipped

- x-intake `gettempdir()` HOME checks (`tests/test_x_intake_smoke_098_100.py`, `103_105`, `106_108`, `112_114`). They assert the child HOME is under the process temp dir. An in-repo TMPDIR still satisfies that. Not a path that resolves outside an outdir.
- `tests/test_pfylib_tmp_cleanup.py` and `tests/support_tmpclean_leaker.py`. Hardcoded `/tmp` is the host-leak detector. Changing it would hide a real leak.
- `docs/TODO.md`. No open local-bench path row. The file is shared with other lanes, so this lane does not add one.
- Pregate. The drop-in says do not run `scripts/pregate.sh`. A GitHub `Runner.Worker` discover was also in progress while this suite ran, so the idle check would have failed.

## Test evidence

Red, before the helper change, `TMPDIR=$PWD/tmp python3 -m unittest tests.test_local_bench.OutdirPathTests`: 3 failures. The inside child stored `tmp/lane-tmpdir-inside-.../demo_model.log`. From `/` that resolved to `/tmp/lane-tmpdir-inside-.../demo_model.log`, outside the outdir.

Green:

- `TMPDIR=$PWD/tmp python3 -m unittest tests.test_local_bench`: Ran 18 tests in 1.341s OK
- `TMPDIR=/dev/shm/pfy-localbench-prove-<pid> python3 -m unittest tests.test_local_bench`: Ran 18 tests in 1.322s OK
- `flock ~/DEVELOP/pfy-mentat/tmp/heavy-1030.lock nice -n 19` with `TMPDIR=$PWD/tmp` and `python3 -m unittest discover -s tests -t .`: Ran 1244 tests in 895.776s OK (skipped=16) EXIT 0. Log: `tmp/suite-localbench-tmpdir.log` (gitignored).

## How it fails and how we recover

`log_path_for_receipt` used to return a repo-relative path when the log was inside the repo. Lane and pregate runs set TMPDIR to the worktree `tmp/`, so the temp outdir is inside the repo. Resolving that relative string from `/` lands on a different path outside the outdir, and the bytes are not the bench log. The string also changed shape when TMPDIR moved outside the repo (absolute there, relative here).

Recovery: store `str(path.resolve())`, or `abspath` if `resolve` raises. The stored path is absolute, has no `..` segment, and `Path(stored).resolve()` stays inside the outdir after `chdir` to `/`. The same rule holds for TMPDIR inside the repo and on `/dev/shm`. `root` remains a parameter so callers do not break. It no longer changes the string. New in-repo receipts carry a machine prefix. Historical receipt files were not rewritten.

## Cross-lane requests

None. No shared file needed an edit.

## Gate

Runtime change in `examples/local-bench/bench.py`. Gate: Tester plus Reviewer. Pregate was not run.

## Next step

Review `4ff2c67`. Do not merge from this lane. No further local-bench TMPDIR item is queued here.
