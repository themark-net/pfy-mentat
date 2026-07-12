# write-guard-mcp

Thin MCP server to **mediate filesystem writes** for agents.  
Design: [docs/ops/write-guard-mcp-design.md](../../docs/ops/write-guard-mcp-design.md) · **ADR-0007**

## Status

**Implemented (v0.1):** policy engine, JSONL audit, stdio MCP tools, unit selftest, in-cage smoke.

```
harness/write-guard-mcp/
  policy.default.yaml
  pyproject.toml
  src/write_guard/     # policy, audit, MCP server
  tests/
```

## Modes

| Mode | Behavior |
|------|----------|
| `off` | Pass-through (no audit) |
| `audit` | **Default** (OQ-0009): allow writes; log attempts; flag secret globs |
| `enforce` | Deny outside roots, secret globs, deny_write_globs; delete default deny |

Env: `WRITE_GUARD_MODE`, `WRITE_GUARD_ROOTS` (colon-separated), `WRITE_GUARD_POLICY`.

## CLI

```bash
cd harness/write-guard-mcp
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
python -m write_guard selftest
python -m write_guard check --path /workspace/.env --op write --mode enforce
python -m write_guard serve   # MCP stdio
```

## In-cage smoke

```bash
make smoke-write-guard
```

## MCP tools

`list_roots`, `list_dir`, `read_file`, `write_file`, `delete_file`, `write_status`

## Cage overlay

See [overlays/write-guard/](../agent-cage/overlays/write-guard/) — fragment for `mcp-servers.yaml` (entry disabled until package is on mcp-host PATH).
