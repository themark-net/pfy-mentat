# Example: write-guard-mcp in agent-cage

**TODO:** T-0031  
**Design:** [docs/ops/write-guard-mcp-design.md](../../docs/ops/write-guard-mcp-design.md) · ADR-0007  
**Package:** [harness/write-guard-mcp/](../../harness/write-guard-mcp/)

## What this proves

Inside agent-cage:

1. Install package editable into a venv  
2. `python -m write_guard selftest` + unittest  
3. **audit**: allow normal + `.env` write (flagged)  
4. **enforce**: deny `.env` write; default deny delete  

MCP stdio server: `python -m write_guard serve` (requires `mcp` dep).

## Run

```bash
make smoke-write-guard
```

Default mode for new envs: **`audit`** (OQ-0009 option 1). `local-only` profile may set `enforce`.
