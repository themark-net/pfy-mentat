# Branch promotion: dev → stage → main

**Status:** Active (ADR-0014)  
**Skill:** `/env-promote` · `scripts/env-promote.sh`  
**Feel:** Classic DevOps environment promotion (dev / staging / prod) with stage as **upgrade rehearsal of production**.

## Model

```text
feature/* ──merge──► dev ──promote──► stage ──accept──► main (tag + fresh build)
                                    ▲                     │
                                    └──── sync stage ─────┘
```

| Branch | Purpose |
|--------|---------|
| **dev** | All immediate work and feature merges |
| **stage** | Copy of **main**, then candidate upgrades from **dev** — “what would production change?” |
| **main** | Release. Only receives accepted **stage**. Fresh build at promote time |

### Rules

1. **No direct dev → main.**  
2. After every successful **stage → main**, **stage := main** (hard reset or ff-only merge).  
3. Prefer PRs for human review; agents may use `scripts/env-promote.sh` with explicit intent.  
4. Pair promotes with eval receipts (`make eval-structural`, `./pfy eval`).

## Commands

```bash
./scripts/env-promote.sh status
./scripts/env-promote.sh to-stage          # merge origin/dev into stage
./scripts/env-promote.sh to-main --tag v0.5.0
./scripts/env-promote.sh sync-stage        # stage := main
```

## Stale feature branches

Fully merged historical `feature/*` tips may be deleted after confirming `--merged main`. Unmerged voice/CI branches that are **superseded** by selective ports on **dev** should be closed via issue note, not force-merged if conflict-heavy.

## Related research

- Environment promotion pipelines (AWS multi-account branching guides)  
- Gitflow (develop + main) simplified to three long-lived lanes  
- One-direction merge policy (dev → stage → prod)
