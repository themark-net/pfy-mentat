# write-guard-mcp (scaffold)

Thin MCP server to **mediate filesystem writes** for agents. Design: [docs/ops/write-guard-mcp-design.md](../../docs/ops/write-guard-mcp-design.md) · ADR-0007.

## Status

**Scaffold only on this branch.** Full stdio MCP implementation is next coding slice.

Planned layout:

```
harness/write-guard-mcp/
  README.md
  policy.default.yaml
  pyproject.toml      # planned
  src/write_guard/    # planned: MCP tools + audit log
```

## Intended run (cage)

```yaml
# overlay snippet for agent-cage mcp-servers.yaml
- name: write-guard
  transport: stdio
  command: python
  args: ["-m", "write_guard"]
  env:
    WRITE_GUARD_MODE: audit   # or enforce
    WRITE_GUARD_ROOTS: /workspace
  enabled: true
```

## Modes

- `audit` — allow writes; log to `/workspace/.write-guard-audit.jsonl`
- `enforce` — deny secrets globs / outside roots; log all attempts
