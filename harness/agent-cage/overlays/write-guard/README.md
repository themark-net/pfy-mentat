# Overlay: write-guard MCP

Adds policy-mediated filesystem tools for agent-cage.

## Status

- **Policy engine + CLI + MCP server code:** `harness/write-guard-mcp/`  
- **In-cage smoke:** `make smoke-write-guard` (does not require mcp-host wiring)  
- **mcp-servers fragment:** `mcp-servers.write-guard.yaml` (write-guard entry disabled until package is on mcp-host PATH)

## Enable later

1. Install `write-guard-mcp` into the agent or mcp-host image.  
2. Set `enabled: true` on the write-guard server.  
3. Optionally disable stock filesystem writes if you want write-guard as the only write path.
