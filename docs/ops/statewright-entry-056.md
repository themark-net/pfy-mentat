# Statewright — Catalog Entry 056

**Status:** Quick-evaluated · cataloged (A / I1)
**Date:** 2026-08-04
**X seed:** https://x.com/i/status/2084511054877380691 (@tom_doerr)
**Repo:** https://github.com/statewright/statewright

## Summary
State machine guardrails that control which tools an AI agent may use in each workflow phase. Define a workflow once; reject out-of-phase tool calls across Claude Code, Codex, Cursor (advisory), opencode (alpha), and Pi. Self-hostable Rust engine + MCP gateway.

## Stage 0
- Self-host: Docker Compose documented under `self-hosted/`
- License: Apache 2.0 (engine/agent); gateway FSL-1.1-ALv2 → Apache in 2029
- Quickstart: workflow JSON + Claude Code plugin / self-host paths

## Scores (initial)
| S1 | S2 | S3 | S4 | Overall | Tier |
|----|----|----|----|---------|------|
| 88 | 70 | 92 | 82 | 85 | A |

## TOOLS.md row (paste under Agent Frameworks)
```
| **Statewright** | Agent Frameworks & Orchestration | https://github.com/statewright/statewright | 88 | 70 | 92 | 82 | 85 | A | #agentic #tool-calling #mcp-compatible #local-first #opencode #state-machine #guardrails | **X Entry 056.** Per-phase tool allow-lists via deterministic Rust state machine + MCP gateway. Hard enforcement on Claude Code/Codex/Pi; opencode alpha; Cursor advisory. Self-host Docker Compose; Apache 2.0 engine/agent (gateway FSL→Apache 2029). Pattern layer over Grok CLI / OpenCode — not primary runtime. |
```

## tools.json object
```json
{
  "name": "Statewright",
  "primary_category": "Agent Frameworks & Orchestration",
  "github": "https://github.com/statewright/statewright",
  "scores": {"s1": 88, "s2": 70, "s3": 92, "s4": 82, "overall": 85},
  "tier": "A",
  "tags": ["agentic", "tool-calling", "mcp-compatible", "local-first", "opencode", "state-machine", "guardrails"],
  "bootstrap_path": null,
  "notes": "X Entry 056 (tom_doerr). Per-phase tool allow-lists via Rust state machine + MCP gateway. Pattern/guard layer over Grok CLI + OpenCode — not primary runtime.",
  "integration_stage": "I1",
  "x_post_id": "2084511054877380691"
}
```

## x-posts.md
See `sources/x-posts-entry-056.md` on this branch.
