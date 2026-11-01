---
name: commit-integrity-and-run-isolation
description: >
  Use this when building or reviewing any loop that reviews a change and then
  commits it (pfy build, review gates, auto-commit agents), when writing its
  tests, or when a test or pregate shares a host with CI. Six commit-integrity
  rules, run-isolation rules, and the tester probe checklist.
argument-hint: "[build | review | probe]"
---

# Commit integrity and run isolation

Use this when code reviews a change and then commits it, when you test that code, or when tests share a host with CI. The rules come from the mvp3 review loop (`scripts/pfy_build_local.py`). Each rule names the commits that implement it.

See [PORT.md](PORT.md). Structural check: `make smoke-grok-skills` ([skill-verification.md](../../../../docs/ops/skill-verification.md)).

## Commit integrity: six rules

The review is a contract. What gets committed must be exactly what the reviewer saw. Anything else fails closed.

1. **The review is a contract on content.** Hash the staged files and compare them with what was reviewed. On a mismatch, refuse the commit.
2. **The whole change must be visible.** If the diff is truncated, has a binary change, or is over budget, refuse. Cap by bytes, not lines: a 250-line cap does not stop one 9000-character line.
3. **Nothing outside the repo.** Do not follow symlinks or hardlinks. A path that resolves outside the worktree fails closed.
4. **Nothing may change files between review and commit.** That includes gates, formatters and hooks. A content or mode change (exec bit) after review is a refusal, not a silent re-stage.
5. **Loud failures with named reasons.** Every refusal has a stable reason string (for example `review-diff-too-large`, `review-binary-change`). A reviewer crash, an empty reviewed set, or a reviewer that writes no verdict is a failure, never a pass.
6. **Staging matches review.** List staged paths with `--no-renames` and NUL separators (`-z`), and set `core.quotepath=false`, so renames and non-ASCII paths compare one to one.

## Rule to commit map

Commits are on `bot/mvp3-review-retry` (not yet on main at the time of writing). Check `git log` on main before you cite them as landed.

| Rule | Commits | What they do |
|------|---------|--------------|
| 1 | `4c7c5f6` | Fail closed when the gate rewrites a reviewed file |
| 2 | `3a550e5` | Refuse a diff over the prompt cap (`review-diff-too-large`) or with a binary change (`review-binary-change`). The cap is 8000 characters today; new code should count bytes |
| 3 | `90b51f3`, `915edf0` | Do not follow symlinks into the review diff. Do not commit a hardlink whose other name is outside the worktree |
| 4 | `4c7c5f6`, `29da017` | Gate rewrite of a reviewed file; gate flip of the exec bit |
| 5 | `d74975a`, `d6de542`, `1fe4365`, `3a550e5` | Fail closed when the review cannot judge, when the reviewed set is empty, when the poster writes no file; named reasons |
| 6 | `3392e78`, `301f786`, `0d3c0fc` | In-scope rename commits cleanly; non-ASCII path kept when listing changes; reviewer prompt shows non-ASCII paths literally |

## Run isolation

- Each run gets its own `TMPDIR`, `HOME` and caches (`UV_CACHE_DIR`, `XDG_CACHE_HOME`). Never share `~/.cache/uv` with CI.
- No asserts on the shared `/tmp` or on the real `HOME`. Store absolute paths so an in-repo `TMPDIR` still works (`4ff2c67` on `bot/mvp-localbench-tmpdir-1031`).
- No pregate while a CI job runs on the same host. Check the process name: `pgrep -x Runner.Worker`. Do not use `pgrep -f` with the word Runner in the pattern; it matches any command line that contains that text, including the one doing the check. Implemented on `bot/mvp-flake-harness2-1031` as `b8ec41d` (exit 3); that commit still uses `pgrep -f` and needs the `-x` form.
- A test that needs full git history uses `self.skipTest` in a shallow clone, never a silent `return` (`a0885ed` on `bot/mvp-flake-harness2-1031`).

## Tester probe checklist

Run each probe through the real CLI with the reviewer stubbed at the HTTP or subprocess boundary. Expected result for every probe: no commit, no push, a named reason, and (for rule 2) zero reviewer calls.

| Probe | Rule | How |
|-------|------|-----|
| Gate rewrite | 1, 4 | The gate edits a reviewed file after the review |
| Symlink | 3 | The agent adds a symlink to a file outside the worktree |
| Hardlink | 3 | The agent adds a hardlink to an outside file |
| Long line | 2 | One 9000-character line plus a tail, under the line cap |
| Many lines | 2 | 200 short lines plus a tail that goes over the byte cap |
| Binary | 2 | Edit a tracked binary file |
| Exec bit | 4 | The gate flips `chmod +x` on a reviewed file |
| Rename | 6 | Rename an in-scope file; it must commit, not report a mismatch |
| Non-ASCII | 6 | Edit tracked `src/café.py`; the prompt shows the literal path |
| Mutant per guard | all | Remove each guard in turn; at least one probe must go red. A guard no probe kills is untested |

## DoD paste line

"Commit integrity: the six rules hold, each refusal has a named reason, and every probe in the checklist plus a mutant per guard is red without the guard. Run isolation: own TMPDIR, HOME and caches; no pregate during CI; skipTest on shallow clones."
