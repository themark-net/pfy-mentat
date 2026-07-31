# ADR-0014: Branch promotion model (dev → stage → main)

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** operator
- **Related:** G8 simple launch, eval gates G0–G2, skill `/env-promote`

## Context

Work accumulated on many short-lived `feature/*` and voice/CI branches while **main** advanced as the only long-lived tip. Operators familiar with DevOps want:

1. **dev** for integration of all current work  
2. **stage** that tracks **production (main)** so upgrades can be rehearsed  
3. **main** as release, promoted only after stage acceptance, with **fresh build**  
4. After release, **stage resynced from main** before new code from dev lands again  

This is **environment promotion**, not pure trunk-based development.

## Decision

Adopt three long-lived branches:

| Branch | Role |
|--------|------|
| `dev` | Integration |
| `stage` | Production mirror + upgrade candidates |
| `main` | Release / production |

Provide `/env-promote` skill + `scripts/env-promote.sh` + ops doc. Default agent work targets **dev**. Releases only **stage → main**.

## Consequences

- Cleaner mental model for “what’s prod” vs “what’s next”.  
- Slightly more ceremony than trunk-only; offsets chaos of many unmerged tips.  
- Stage must not become a second long-lived feature dump — always resync after release.

## Rejected alternatives

| Option | Why not |
|--------|---------|
| main-only + tags | No place to rehearse upgrades safely |
| Gitflow full (release/*, hotfix/* always) | Too heavy for this catalog size; optional later |
| Environment branches that never match prod | Stage would lie about upgrade impact |
