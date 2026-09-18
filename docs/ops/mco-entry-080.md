# Ops notes — Entry 080 MCO

## Stage 0
- Self-host <5 min: yes (`npx @tt-a1i/mco@latest install` or clone + `pip install -e .`)
- License: MIT
- Hello-world: `mco doctor --json`, `mco review --repo . --prompt "..." --providers claude,codex,pi`

## Suggested TOOLS.md row (Agent Frameworks & Orchestration)

| Tool | Category | Stage scores | Tier | Notes / Tracking |
|------|----------|--------------|------|------------------|
| MCO | Multi-Model & Parallel Orchestration | S1=85 S2=70 S3=88 S4=78 → ~81 | A/B | CLI-first parallel agents + raw-answer comparison. Depends on provider CLIs. Pin latest main or npm. Entry 080. |

## data/tools.json sketch
```json
{
  "name": "MCO",
  "repo": "https://github.com/mco-org/mco",
  "license": "MIT",
  "category": "Agent Frameworks & Orchestration",
  "subcategory": "Multi-Model & Parallel Orchestration",
  "scores": {"S1": 85, "S2": 70, "S3": 88, "S4": 78, "overall": 81},
  "tier": "A/B",
  "x_post_entry": "080",
  "install": "npx @tt-a1i/mco@latest install",
  "notes": "Parallel selected agents/models; retains raw answers; review/implement workflows. Provider CLIs required."
}
```

## Merge steps
1. Append content of `sources/entries/080-mco.md` into `sources/x-posts.md` (or keep as standalone entry file if that is the current convention).
2. Add TOOLS.md row + tools.json object on merge or follow-up.
3. No TODO deeper-eval item unless smoke fails.
