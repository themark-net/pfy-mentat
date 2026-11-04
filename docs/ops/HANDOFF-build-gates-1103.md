# Handoff: lanes/build-gates-1103 (2026-11-03)

## What changed
- `scripts/pfy_gate_jobs.py`: `run` pins a SHA, runs Tester and Reviewer as headless grok
  Build jobs in detached worktrees, and writes fail-closed verdicts. `check` is what bots call.
- `scripts/gate_prompts/{tester,reviewer}.md`: job prompts modeled on the 533a634 and a205d2b FAILs.
- `tests/test_gate_jobs.py`: 19 behavior tests with fake grok scripts (every fail-closed path,
  isolation, SHA pinning, stale-verdict reuse, job logs).
- Docs: `GATE-VERDICTS.md` (consumption and the 533a634 replay), `BUILD-GATE-TRIALS-1103.md`.

## How it fails and recovers
- Timeout, crash, max-turns, moved HEAD, missing or foreign-SHA verdict: FAIL with a REASON.
  Recovery is to rerun `run` for the same SHA (old files are deleted first). Read
  `<out>/<sha>/<job>.log` for why. Unknown SHA or base exits 2 before any job.

## Left to do
- Tester ran out of turns at 40 on the replay: default the tester to 80, or split probes.
- Not wired into `pfy` or the bots yet; the bots still need their prompts pointed at `check`.
- Headroom: catalog only. grill-me: optional pre-ticket step, not wired into lanes.mts.
- The lane reviewer gave no verdict twice on G1 (exit 143); landed by hand after review and
  the full exit test passed.
