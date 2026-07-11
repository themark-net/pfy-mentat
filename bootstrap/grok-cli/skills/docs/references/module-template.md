# Module documentation template

Save as `docs/modules/<name>.md`.

```markdown
# Module: <package.or.path>

**Architecture layer:** <e.g. Integrations / Persistence / Intelligence / CLI>  
**Code:** `<path>`  
**Related ADR / Decisions:** <IDs>

## Operator

### What it does

One short paragraph.

### How to run

```bash
# commands
```

### Failure modes

| Symptom | Likely cause | Recovery |
|---------|--------------|----------|
| … | … | … |

## Configuration / variables

| Name | Where | Purpose |
|------|-------|---------|
| `ENV_VAR` | `.env` → `config.py` | … |
| `field` | code constant / CLI flag | … |

## Agent

### Entry points

- `function_or_class` — role

### Data shapes

- Input / output structures, DB tables, file formats

### Callers / callees

- Who calls this; what this calls (one hop is enough unless critical path)

### Invariants

- Must hold true (cite Decision/ADR IDs)

### Extension points

- Safe places to add behavior

### Do not

- Forbidden changes (e.g. mutate sacred user files, auto-submit, break raw round-trip)
```
