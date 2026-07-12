---
name: one-shot
description: >
  Execute a single request with minimal user questions: write Definition of Done,
  check prerequisites (env profile, agent-cage or waived lab), iterate cheap
  local/static/cage verification before cloud, stop when green or budget/blocker.
  Use when the user runs /one-shot, says one-shot, unattended until green,
  minimize questions, or auto-iterate until working. Requires
  docs/ops/one-shot-workflow.md in this repo.
argument-hint: "<request or DoD>"
---

# /one-shot — Unattended-until-green (guardrailed)

Full rules: `docs/ops/one-shot-workflow.md` · ADR-0008.

## On invoke

1. **Restate** the request in one short paragraph.
2. **Write DoD** — numbered pass/fail checks (commands or observable outcomes).
3. **List assumptions** you will not ask about.
4. **Prerequisites** (fail closed):
   - `DEPLOY_PROFILE` / `make env-check` if stack work
   - If DoD needs isolation: agent-cage up/status **or** explicit host-only waiver in DoD
   - No missing secrets for profile when cloud tier required
5. **Cost ladder:** tier 0 static → local model → cage smoke → mid cloud → heavy cloud (respect profile max).
6. **Loop:** implement → cheapest verify → fix; max **8** iterations; max **3** identical failures then escalate tier or stop.
7. **Ask the user only if:** hard blocker, missing secret, irreversible product fork, or budget exhausted.
8. **Finish:** report green DoD checklist, paths changed, assumptions, remaining OQ/TODO if any.

## Do not

- Infinite retries
- Cloud before local/static checks when avoidable
- Scope creep beyond DoD
- Commit secrets; skip triple-write on catalog seeds
- Run destructive host ops outside workspace/cage policy

## Report template

```markdown
## One-shot result: PASS | FAIL | BLOCKED
**DoD:** ...
**Iterations:** n
**Highest cost tier used:** 0-4
**Assumptions:** ...
**Changes:** paths...
**Verify commands:** ...
**Human needed (if any):** one question only
```
