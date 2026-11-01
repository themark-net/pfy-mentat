# Common rules for Build drop-ins

These rules apply to every drop-in that describes the gate path. A drop-in finish line points here instead of restating the fast-forward rule.

## Gate path before a fast-forward

Docs, eval, and test-only changes are gated by pregate plus Reviewer. Runtime changes are gated by Tester plus Reviewer. There is no PR. The bot fast-forwards `main` only after the gate for that pin passes.

Local pregate does not dispatch GitHub `eval-structural`. It runs in a full worktree. Both G0 jobs check out with the default depth of `actions/checkout` (depth 1) and both run `python3 -m unittest discover -s tests`. A docs-only pin that adds or edits tests under `tests/` is still on that CI path. Pregate PASS on a full worktree does not replace the dispatch.

Before a fast-forward of a fix pin that adds or edits tests under `tests/`:

1. Dispatch `eval-structural` (`workflow_dispatch`) at that fix pin.
2. Wait until both G0 jobs have a conclusion on that SHA: `G0 (ubuntu-24.04)` and `G0 (self-hosted nimo)`.
3. Do not fast-forward while either job is queued or in progress, or while `G0 (ubuntu-24.04)` failed.

The workflow sets `continue-on-error` on `G0 (self-hosted nimo)`, so a green workflow is not the same as both jobs succeeding. Read each job.

- A nimo job that ran and failed blocks the fast-forward.
- A nimo job that never started because the runner was offline is recorded as not run. It is not a pass. It does not block after `G0 (ubuntu-24.04)` has passed on that same fix pin.

How this fails: the bot fast-forwards a test-adding pin because pregate passed, and the depth-1 checkout later fails a git-history test. Recovery: dispatch `eval-structural` at the fix pin, wait for both G0 jobs as above, and fast-forward only a SHA those jobs have already concluded on.

See [PREGATE.md](../ops/PREGATE.md) and [eval-gates-and-ux-uat.md](../ops/eval-gates-and-ux-uat.md).
