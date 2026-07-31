# Promotion model reference

## Why not trunk-only?

Trunk-based development is fine for many products. This catalog/agent monorepo needs:

1. A **stable release tip** (`main`) operators can pin.  
2. A place to **rehearse upgrades** against that tip (`stage`).  
3. A place for **messy integration** without pretending it is production (`dev`).

## Hotfixes

Production hotfix: branch from `main` → fix → PR to `main` **and** merge into `dev` and `stage` (or re-sync stage from main after hotfix release). Prefer: fix on branch from main → stage for verify → main → sync-stage → merge main into dev.

## Feature branches

`feature/*` cut from **dev**, merge back to **dev**. Do not open long-lived feature branches from main unless the change is a hotfix.

## Alignment with eval gates

| Promote | Minimum gate |
|---------|----------------|
| feature → dev | author judgment + prefer structural green |
| dev → stage | G0 structural (+ G1 if deploy spine touched) |
| stage → main | G0 + G1; G2 human UAT when product UX changes |
