# Architecture Decision Records (ADR)

**Store layout:** multi-file under `docs/adr/` (preferred for this project).  
**Process:** Grok skill `/adr` — full template and lifecycle in skill references.

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [0001](0001-process-docs-and-adr-layout.md) | Process docs + multi-file ADR layout | Accepted | 2026-07-11 |
| [0002](0002-grok-cli-primary-interface.md) | Grok CLI as primary operator interface | Accepted | 2026-07-11 |
| [0003](0003-default-pinned-commit-tracking.md) | Default tool tracking = pinned commit | Accepted | 2026-07-11 |
| [0004](0004-first-party-grok-bootstrap-package.md) | First-party Grok bootstrap under `bootstrap/grok-cli/` | Accepted | 2026-07-11 |
| [0005](0005-light-process-framework-not-heavy-tools.md) | Keep light DESIGN/ADR/TODO/OQ framework; do not replace with heavy tools | Accepted | 2026-07-11 |
| [0006](0006-deployment-profiles.md) | Deployment profiles local-only → max-performance + env registry | Accepted | 2026-07-12 |
| [0007](0007-write-guard-mcp-layer.md) | Write-guard MCP as filesystem write mediation layer | Accepted (design) | 2026-07-12 |

## How to add

1. Next free `NNNN` (never reuse).
2. Create `docs/adr/NNNN-slug.md` from the skill template.
3. **Required:** rejected alternatives with concrete reasons.
4. Add a row to this index.
5. If layering changes, update `docs/ARCHITECTURE.md` and relevant DESIGN sections in the same change set.
6. Link related OQs; promote answered architectural OQs to ADR.

## Lifecycle

`Proposed` → `Accepted` | `Rejected`  
`Accepted` → `Superseded by NNNN` (new entry required; never silent overwrite)
