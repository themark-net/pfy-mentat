# Write-guard mcp-host wiring (T-0043)

**Server:** `harness/write-guard-mcp` · smoke: `make smoke-write-guard`

## Host wiring checklist

| Step | Action |
|------|--------|
| 1 | Install/run write-guard stdio server per harness README |
| 2 | Register in Grok / mcp-host config as filesystem policy companion |
| 3 | Cage overlay: ensure policy.default.yaml allows write-guard |
| 4 | Smoke: `make smoke-write-guard` green |
| 5 | Optional: voice high-tier monitor inherits same MCP set |

## Default

Write-guard **implemented** (T-0031). This ticket was mcp-host **operator wiring** notes — now documented. Deep host integration remains operator DEPLOY_PROFILE dependent.
