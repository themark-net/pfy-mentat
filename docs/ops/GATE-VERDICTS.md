# Gate verdicts: how the Tester and Reviewer bots consume Build-job results

Testing and review run as two headless Grok Build jobs on nimo. The bots do not
run the suite or read the diff line by line. They read two verdict files and
spot-check them.

## Producing verdicts

```
python3 scripts/pfy_gate_jobs.py run --repo <checkout> --sha <sha> --base <base> \
  [--out <dir>] [--grok-cmd "grok --output-format json"] [--timeout 1800] \
  [--max-turns N] [--brief <file>] [--jobs tester,reviewer]
```

- The SHA is resolved to the full 40 chars. An unknown SHA or base exits 2 and runs nothing.
- Each job gets its own detached worktree at exactly that SHA under `<checkout>/tmp/gate-jobs/`,
  removed afterwards (`--keep` leaves it). The caller checkout is never touched.
- Prompts: `scripts/gate_prompts/tester.md` and `reviewer.md` (modeled on the 533a634 and
  a205d2b FAILs). The job writes a raw verdict to `$GATE_VERDICT`; env also has
  `GATE_SHA`, `GATE_BASE`, `GATE_JOB`, `TMPDIR=<worktree>/tmp`.
- Output in `<out>/<fullsha>/` (default `<checkout>/tmp/gate-verdicts/`):
  `tester.md`, `reviewer.md` (written by the runner), `<job>.raw.md` (written by the job),
  `<job>.log` (job stdout and stderr), `summary.json`.
- Exit 0 only if both jobs PASS.

## Fail-closed rules

The runner writes the header, never the job:

```
VERDICT: PASS|FAIL
SHA: <full sha>
JOB: tester|reviewer
REASON: ok|timeout|crash|sha-moved|no-verdict|sha-mismatch
```

Checked in this order, first hit wins:

| REASON | When |
|---|---|
| timeout | the job ran past `--timeout` (process group killed), even if it wrote PASS |
| crash | nonzero exit or the command could not start, even if it wrote PASS |
| sha-moved | worktree HEAD is not the pinned SHA after the job |
| no-verdict | no raw file, or no line exactly `VERDICT: PASS` / `VERDICT: FAIL` |
| sha-mismatch | no `SHA: <pinned sha>` line, or any `SHA:` line naming another commit |
| ok | the job's own PASS or FAIL stands |

A re-run deletes that SHA's previous raw, final, log and summary files first, so a job
that writes nothing can never inherit an older PASS.

## What a bot does

1. `python3 scripts/pfy_gate_jobs.py check --sha <sha> --out <dir>`. Exit 0 means both files
   exist, both say `VERDICT: PASS`, `REASON: ok` and `SHA:` equal to the SHA you asked about.
   Anything else exits 1 and prints which job failed and why. Treat exit 1 as FAIL.
2. Read `tester.md` and `reviewer.md` Blockers sections. Post the verdict on the PR as-is.
3. Spot-check one claim per file: rerun one command from the Commands section, or open one
   cited file:line. If the spot-check disagrees, the gate is FAIL and the disagreement goes
   in the post.
4. Never accept a verdict for a SHA other than the PR head. A new push means a new run.

## Behavior run: replay of 533a634 (base bedb5ce), 2026-11-03 22:07 to 22:26 PT

`run --sha 533a634 --base bedb5ce --grok-cmd "grok --output-format json" --timeout 1800 --max-turns 40`
exited 1, `summary.json` verdict FAIL.

- reviewer: `FAIL ok`, 34 turns, 892 s, $0.787. Its own Blockers match tonight's human
  FAILs: `Mark:` recovery text at pfy_build_cloud.py:619/634 locked in by tests, no
  HANDOFF doc in the range, `.pytest_cache`/`.pyc` writes counted as gate-rewrote, and C4's
  star-import exit test going red on a patch-anchor mismatch rather than the lock.
- tester: `FAIL crash`, hit `--max-turns 40` (grok exits nonzero) after 1108 s, $1.052, with
  no verdict written. Fail-closed worked, but the FAIL was not earned by evidence. Its log
  shows it had already found a failing unit test masked by a shell `echo`. Use
  `--max-turns 80` for the tester on lanes of this size.
