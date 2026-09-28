---
name: best-effort-and-bot-budget-build-max
description: >
  Use this when choosing BEST_EFFORT versus GATED, allocating implement work
  to Grok Build or Cursor, or working in parallel with an open founder Build
  session. Land reversible work; do not share that checkout.
argument-hint: "[path | isolate]"
---

# Best effort + bot-budget / Build-max

Standing doctrine (2026-09-25; concurrent-Build + CEO pushback). Portable SoT for Build, cage, and Cursor.

See [PORT.md](PORT.md). Structural check: `make smoke-grok-skills` ([skill-verification.md](../../../../docs/ops/skill-verification.md)).

## Core

- Pain is almost never “code quality” — it is **decision and gate latency**.
- Prefer **progress that drives goals** over ceremony. Git tracks history; revert/rollback is allowed when work is visible (branches/PRs).
- **A dead Grok Bot limit is worse than a full Grok Build limit.** Full Build = usage maximized. Empty Bot = wasted turns chatting and gating.
- Cadence goal: the founder drives Build, bot usage stays meet-not-exceed, the org still ships. If parallel gets too hairy (merge thrash, bot burn, thrashing an open Build tip), **CEO pushes back** — pause or serialize slices without waiting for the founder to notice.

## Two paths

| Path | When | Bar |
|------|------|-----|
| **BEST_EFFORT** | Default for private dogfood, docs, visibility drafts, reversible feature on tracked branches | “Does this drive our goals?” Ship/land; fix forward or revert. Skip architecture/UI/test theater that is not load-bearing. |
| **GATED** | Public release, money, legal/IP, irreversible prod, multi-user blast radius | Keep Reviewer/Tester/Design gates. Still minimize bot turns — hand heavy work to Build/Cursor. |

CEO/PM pick the path in the RELEASE note. If unspecified → **BEST_EFFORT** while Feature STAND BY or private dogfood.

## Where the work runs

1. Org bots **coordinate only**: short DoD, route, MERGE-CLEAR, blocker tips. This Build/Cursor session does the implement.
2. Dial bot usage to **meet but not exceed** bot limits. Prefer fewer, denser turns. Use local scripts over multi-agent ping-pong.
3. **Maximize Build (and Cursor) usage** for implement. Cursor Pro does not refill bot limits.
4. If the choice is “another gate round” versus “implement from a one-line DoD” → implement.

## Concurrent with an open founder Grok Build session

The founder may keep Build sessions open **and** other agents may work in parallel. That checkout is primary. Git is the handoff.

### Isolation rules (required)

1. **Never** share the founder’s live working tree / dirty Build checkout. No `git commit` / reset / stash on the branch that session is mid-work on.
2. Work goes on a **named branch** (or cloud remote-only, or a `tmp/` worktree). Prefer remote branch + PR over touching that checkout’s local files.
3. **Rebase/merge around that tip** when it lands; on conflict, prefer the founder Build tip unless this PR is already CI-green and the other change is unrelated — then escalate to CEO, not the founder.
4. Handoff = PR + short `docs/PENDING-HANDOFF.md` note.
5. Feature STAND BY still means no auto Feature GO / public ship without a founder RELEASE — concurrent implement on branches is allowed under BEST_EFFORT.

### CEO throttle

If concurrent work gets hairy — repeated tip conflicts, bot quota burned on rebase/coordination, or progress stalls — CEO serializes: park non-critical slices, keep the founder Build primary, resume when the tip is stable. Do not ask the founder for permission to throttle.

### Anti-patterns

- Two agents editing the same uncommitted files an open Build session is using.
- Force-pushing the founder’s Build branch or `main`.
- Waiting on an open Build session instead of branching.
- Continuing parallel after thrash without CEO throttle.

## Anti-patterns (general)

- Burning bot quota on Reviewer/Tester/Design chatter while Build quota sits idle.
- Asking the founder to decide reversible BEST_EFFORT items.
- Treating every merge as GATED by default.

## DoD paste line

```
Path: BEST_EFFORT unless the RELEASE note says GATED (public, money, legal, irreversible). Named branch + PR. Do not touch an open founder Build checkout. No Feature GO.
```

## How this fails / how we recover

| Risk | Failure | Recovery |
|------|---------|----------|
| Shared dirty checkout | Commit, reset, or stash lands on the open Build branch | Stop. Move the work onto a named branch or `tmp/` worktree. Do not stash or reset that checkout. |
| Tip conflict | Rebase fights an unrelated founder commit | Prefer the founder tip. Escalate to CEO only if this PR is already CI-green and the change is unrelated. |
| Gate theater on docs/skills | A BEST_EFFORT port waits on a full GATED review novel | Land the branch/PR. Structural bar is `make smoke-grok-skills`. |
| Feature GO by accident | A STAND BY branch is treated as a public ship | PR states no Feature GO. No release tag, no catalog row. |
