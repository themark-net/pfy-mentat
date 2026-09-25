# Best effort and bot-budget / Build-max

**Purpose:** Ops note for gate choice and concurrent git isolation. Not a slash skill.  
**Standing:** 2026-09-25 (concurrent Build + CEO pushback).  
**Portable skills:** test and UI standings live under `bootstrap/grok-cli/skills/`. This file stays prose.

## Core

- Pain is almost never “code quality” — it is **decision and gate latency**.
- Prefer **progress that drives goals** over ceremony. Git tracks history; revert/rollback is allowed when work is visible (branches/PRs).
- **A dead Grok Bot limit is worse than a full Grok Build limit.** Full Build = usage maximized. Empty Bot = wasted turns chatting and gating.
- Cadence goal: the founder drives Build, bot usage stays meet-not-exceed, the org still ships. If parallel gets too hairy (merge thrash, bot burn, thrashing the open Build tip), **CEO pushes back** — pause or serialize slices without waiting for the founder to notice.

## Two paths

| Path | When | Bar |
|------|------|-----|
| **BEST_EFFORT** | Default for private dogfood, docs, visibility drafts, reversible feature on tracked branches | “Does this drive our goals?” Ship/land; fix forward or revert. Skip architecture/UI/test theater that is not load-bearing. |
| **GATED** | Public release, money, legal/IP, irreversible prod, multi-user blast radius | Keep Reviewer/Tester/Design gates. Still minimize bot turns — hand heavy work to Build/Cursor. |

CEO/PM pick the path in the RELEASE note. If unspecified → **BEST_EFFORT** while Feature STAND BY or private dogfood.

## Bot budget (Grok Bot org)

1. Bots **coordinate only**: short DoD, route, MERGE-CLEAR, blocker tips. No large implement, long research, or gate novels in bot chat.
2. Dial bot usage to **meet but not exceed** bot limits. Prefer fewer, denser turns. Use local scripts over multi-agent ping-pong.
3. **Maximize Build (and Cursor) usage** for implement. Cursor Pro does not refill bot limits.
4. If choosing between “another bot gate round” and “spawn Build with a one-line DoD” → spawn Build.

## Concurrent with an open founder Grok Build session

The founder may keep Build sessions open **and** bots may work in parallel. That checkout is primary — bots work around it. Git is the handoff.

### Isolation rules (required)

1. **Never** share the founder’s live working tree / dirty Build checkout. No `git commit` / reset / stash on the branch that session is mid-work on.
2. Bot/Cursor work goes on a **named branch** (or cloud remote-only, or a `tmp/` worktree under the project). Prefer remote branch + PR over touching that checkout’s local files.
3. **Rebase/merge around that tip** when it lands; on conflict, prefer the founder Build tip unless the bot PR is already CI-green and the other change is unrelated — then escalate to CEO, not the founder.
4. Handoff = PR + short `docs/PENDING-HANDOFF.md` note. Visibility drip (SSH push + MCP drafts) stays.
5. Feature STAND BY still means no auto Feature GO / public ship without a founder RELEASE — concurrent implement on branches is allowed under BEST_EFFORT.

### CEO throttle (pushback)

If concurrent work gets hairy — repeated tip conflicts, bot quota burned on rebase/coordination, or progress stalls — CEO serializes: park non-critical bot slices, keep the founder Build primary, resume when the tip is stable. Tell the founder once after the fact only if it changed what they should expect; do not ask permission to throttle.

### Anti-patterns

- Two agents editing the same uncommitted files the open Build session is using.
- Force-pushing the founder’s Build branch.
- Burning bot quota to “wait for Build to finish” instead of branching.
- Continuing parallel after thrash without CEO throttle.

## Anti-patterns (general)

- Burning bot quota on Reviewer/Tester/Design chatter while Build quota sits idle.
- Asking the founder to decide reversible BEST_EFFORT items.
- Treating every merge as GATED by default.

## How this fails / how we recover

| Risk | Failure | Recovery |
|------|---------|----------|
| Shared dirty checkout | Bot commit or reset lands on the open Build branch | Stop. Move work onto a named branch or `tmp/` worktree. Do not stash or reset that checkout. |
| Tip conflict | Rebase fights an unrelated founder commit | Prefer the founder tip. Escalate to CEO only if the bot PR is already CI-green and the change is unrelated. |
| Gate theater on docs/skills | BEST_EFFORT port waits on a full GATED review novel | Land the branch/PR. Structural bar is `make smoke-grok-skills`. |
| Feature GO by accident | STAND BY branch is treated as a public ship | PR states Feature STAND BY. No release tag, no catalog row. |
