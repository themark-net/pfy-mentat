# Bumblebee as coding-safety assist

**Source:** Entry 069 · TOOLS.md **Bumblebee** (Perplexity MCP/supply-chain scanner)  
**Posture:** Read-only scanner for packages, extensions, **MCP configs**. Pair with write-guard; no default install required.

## Why it helps design/coding agents

Agents install MCP servers and deps. Bumblebee-class scans reduce “trusted by default” on `mcp` config and package trees.

## Defaults (no human)

| Step | Action |
|------|--------|
| Today | This doc + TOOLS row; use write-guard + cage policy |
| Next automation | Optional `make smoke-bumblebee` if Go binary install is one-liner in cage |
| Not default | Block all MCP installs pending scan (too high friction without smoke) |

## Loop for future agents

```text
Adding MCP or npm/pip tool?
  → Prefer catalog row + pin
  → If binary trivial: smoke + NDJSON baseline
  → Else: docs only; continue coding
```

No operator question unless scan would delete/quarantine artifacts (blast radius).
