# Architecture snapshot — {{PROJECT_NAME}}

**Last updated:** {{DATE}}  
**Design authority:** [DESIGN.md](DESIGN.md)  
**Decision authority:** [adr/](adr/README.md)

Keep this file short. If layering or boundaries change, accept an ADR and update DESIGN §4.

## Purpose

{{VISION_ONE_LINER}}

## Data flow (delivered)

```text
{{DATA_FLOW}}
```

## Layout map

| Area | Path | Notes |
|------|------|--------|
| Process | `docs/` | Design, ADR, TODO, OQ |
| Application | *(fill)* | |

## Delivered vs not

| Delivered | Not yet |
|-----------|---------|
| Process docs bootstrap | *(fill)* |

## Extension points

- New module → docs under `docs/modules/` + TODO/OQ as needed
- Architecture pivot → ADR first

## Forbidden without ADR

- Second parallel decision log outside `docs/adr/`
- Silent overturn of Accepted decisions
