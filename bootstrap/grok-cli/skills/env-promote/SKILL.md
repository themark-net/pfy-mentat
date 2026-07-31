---
name: env-promote
description: >
  Environment / branch promotion for pfy-mentat: dev (integration) → stage
  (upgrade rehearsal of production) → main (release). Use when the user runs
  /env-promote, asks to promote stage to main, open a release, sync stage from
  main, or land feature work onto the right long-lived branch. Portable pattern
  for any repo using three-lane promotion.
argument-hint: "[status|to-stage|to-main|sync-stage|help]"
---

# env-promote — dev → stage → main

You enforce **one-way promotion** with a **production-faithful stage**. This matches common DevOps practice (environment promotion / Gitflow-inspired three lanes) adapted for a catalog + agent stack.

## Lanes

| Branch | Environment role | What lands here |
|--------|------------------|-----------------|
| **dev** | Integration / “dev env” | Features, hotfixes-in-progress, experiments after PR or direct agent work |
| **stage** | Staging / upgrade rehearsal | Only packages that **already match main**, then **candidate upgrades** from **dev** for acceptance |
| **main** | Production / release | **Only** accepted content from **stage**, via fresh build + tag |

### Critical stage rule (user intent)

1. **stage starts as a mirror of main** (what production is running).  
2. When testing an upgrade, promote **selected** changes **dev → stage** (merge or PR). Stage then shows *exactly what production would change*.  
3. After **human/automated acceptance** on stage: promote **stage → main** with a **fresh build** (no reusing dirty artifacts).  
4. Immediately **reset stage from main** so stage never accumulates unreleased drift.  
5. Never merge **dev → main** directly. Never merge **main → dev** as a substitute for rebasing feature work (optional: periodically merge main→dev to keep dev current).

```text
feature/* ──► dev ──► stage ──► main
                      ▲           │
                      └───────────┘  (sync stage := main after release)
```

## Research lineage (name the pattern)

- **Environment promotion** / **promotion pipeline** (AWS multi-account, classic CI/CD): code moves up environments; never sideways into prod.  
- **Gitflow-inspired** (nvie): long-lived develop + release + main — we simplify to three branches without release/* unless needed.  
- **Stack Overflow / Beanstalk classic**: development → staging → production, merges **one direction** only.  
- Improvement for this repo: pair each promote with **eval gates** (G0 structural, G1 deploy-ready, G2 human UAT) and **receipts** under `pipelines/eval/`.

## Operator commands (this repo)

```bash
# Status of the three lanes
./scripts/env-promote.sh status

# Propose/dev integration is normal git on dev
git checkout dev && git pull && # land work

# Promote candidate upgrades to stage (merge dev into stage)
./scripts/env-promote.sh to-stage

# After acceptance: promote stage → main (tag + fresh verify) then resync stage
./scripts/env-promote.sh to-main --tag vX.Y.Z

# Force stage := main (post-release or repair drift)
./scripts/env-promote.sh sync-stage
```

Make wrappers (if present): `make promote-status`, `make promote-to-stage`, `make promote-to-main TAG=…`, `make promote-sync-stage`.

## Agent checklist when asked to promote

1. **Identify lane** of current work (`git branch --show-current`).  
2. If on a feature branch: merge/PR into **dev** only.  
3. Before **to-stage**: run `make eval-structural` (and `./pfy eval` if catalog touched).  
4. Before **to-main**: confirm stage was tested; run structural + integration-change; note build is **fresh** (no copying of prior release artifacts).  
5. After **to-main**: run **sync-stage** so stage == main again.  
6. Log a short receipt in chat: SHAs of dev/stage/main, gates run, tag if any.

## Do not

- Promote broken structural eval.  
- Commit secrets.  
- Squash history in a way that erases stage acceptance evidence without a tag.  
- Leave stage ahead of main after a successful release (always resync).

## Related

- [docs/ops/branch-promotion.md](../../../docs/ops/branch-promotion.md)  
- ADR-0014  
- G8 `./pfy` stays the *runtime* simple surface; this skill is the *git/env* simple surface.
