# Session → golden-task capture (sample, not every turn)

**Status:** Workflow + semi-auto helper · issue #32  
**Policy:** [local-model-storage-and-eval.md](local-model-storage-and-eval.md)

## When to capture

High-signal only: P0/P1 TODO close, OQ/ADR resolution, new eval lane, product-surface change.

## Semi-auto path

```bash
# Draft a card from args (edit before commit)
python3 scripts/draft_golden_task.py \
  --id GT-0002 \
  --title "short title" \
  --scale docs \
  --human "operator ask..." \
  --artifact docs/ops/example.md
python3 examples/eval-harness/validate_golden_tasks.py
```

Cage sessions (T-0047): export notes from `make cage-grok-sessions` / session files, then paste human request + agent bullets into the draft.

## Filter

Do **not** log every chat turn. Prefer structured cards over raw transcripts.

## Agent hook (GAP-06 / #43)

When closing a **P0/P1** issue or resolving an OQ/ADR:

```bash
python3 scripts/draft_golden_task.py \
  --id GT-NNNN \
  --title "short" \
  --human "…" \
  --artifact path/to/file
python3 examples/eval-harness/validate_golden_tasks.py
```

Do not draft for every close. Sample high-signal only.
