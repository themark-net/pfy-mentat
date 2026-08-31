# Ops notes — Entry 082 Axon

## Stage 0
- Self-host <5 min: yes (`pip install axoniq` or `uv add axoniq`; `axon analyze .` then `axon ui` / `axon serve --watch`)
- License: MIT
- Hello-world: analyze → local dashboard (localhost:8420) or MCP server for agents
- Fully local: KuzuDB + local embeddings; no cloud/API keys required

## Suggested TOOLS.md row (Context & Memory / Codebase Knowledge Graph)

| Tool | Category | Stage scores | Tier | Notes / Tracking |
|------|----------|--------------|------|------------------|
| Axon | Codebase Knowledge Graph & MCP | S1=90 S2=82 S3=92 S4=85 → ~88 | A | Structural KG + MCP tools (query/context/impact/dead-code). Local KuzuDB. Compare Graphify / codebase-memory-mcp. Entry 082. |

## data/tools.json sketch
```json
{
  "name": "Axon",
  "repo": "https://github.com/harshkedia177/axon",
  "license": "MIT",
  "category": "Context & Memory",
  "subcategory": "Codebase Knowledge Graph & MCP",
  "scores": {"S1": 90, "S2": 82, "S3": 92, "S4": 85, "overall": 88},
  "tier": "A",
  "x_post_entry": "082",
  "install": "pip install axoniq",
  "notes": "Indexes codebase to structural knowledge graph (KuzuDB). MCP tools for agents + visual UI. Fully local."
}
```

## Merge steps
1. Keep `sources/entries/082-axon.md` (or fold into x-posts.md).
2. Add TOOLS.md row + tools.json object on merge or follow-up.
3. Optional: queue comparative smoke vs Graphify / codebase-memory-mcp in TODO if desired.
