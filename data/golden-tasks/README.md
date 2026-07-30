# Golden tasks (repo-grounded model eval)

**Policy:** [docs/ops/local-model-storage-and-eval.md](../docs/ops/local-model-storage-and-eval.md) (OQ-0008)

Sample of **human request → agent work** already done on this repo. Candidate models are scored on **proximity** to the original outcome — not only external benches.

## Schema (per card)

`data/golden-tasks/GT-NNNN-slug.json`:

```json
{
  "id": "GT-0001",
  "title": "short title",
  "created": "2026-07-30",
  "scale": "orchestration|multi_file|single_code|docs",
  "human_request": "verbatim or tight paraphrase of operator ask",
  "agent_tasks": ["bullet list of what the agent did"],
  "artifacts": [
    {"kind": "commit|file|issue|doc", "ref": "path or url", "note": "why it proves success"}
  ],
  "acceptance_checks": [
    "deterministic check a scorer can run (file exists, status field, etc.)"
  ],
  "source_session": "optional link or date",
  "replay_prompt": "prompt to give the candidate model/agent",
  "notes": "sampling reason"
}
```

## Index

| ID | Scale | Title |
|----|-------|-------|
| [GT-0001](GT-0001-oq-batch-integration-stages.json) | orchestration | Resolve OQ batch + integration stages + model policy |

## Adding a card

1. Prefer P0/P1 work, OQ resolutions, ADR-class changes.  
2. Do **not** log every chat turn.  
3. Keep `acceptance_checks` machine-checkable when possible.  
4. Link commits/issues; avoid pasting secrets.

## Automation (queued)

- Manual cards first (feasible now).  
- Later: export from cage sessions / OpenCode logs → draft cards.  
- Lane: `golden_replay` in `data/eval-lanes.json` (planned).
