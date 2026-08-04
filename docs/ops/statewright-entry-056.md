# Statewright — Catalog Entry 056

**Status:** Quick-evaluated · cataloged (A / I1)  
**Date:** 2026-08-04  
**X seed:** https://x.com/i/status/2084511054877380691 (@tom_doerr)  
**Repo:** https://github.com/statewright/statewright

## Summary
State machine guardrails that control which tools an AI agent may use in each workflow phase. Define a workflow once; reject out-of-phase tool calls across Claude Code, Codex, Cursor (advisory), opencode (alpha), and Pi. Self-hostable Rust engine + MCP gateway.

Tagline: *Agents are suggestions, states are laws.*

## Stage 0
- **Self-host:** Docker Compose under `self-hosted/`
- **License:** Apache 2.0 (engine/agent); gateway FSL-1.1-ALv2 → Apache in 2029
- **Quickstart:** workflow JSON + Claude Code plugin / self-host paths

## Scores (initial)
| S1 | S2 | S3 | S4 | Overall | Tier |
|----|----|----|----|---------|------|
| 88 | 70 | 92 | 82 | 85 | A |

## Integration notes
- Pattern / guard **layer** over Grok CLI + OpenCode — **not** primary runtime
- Hard enforcement: Claude Code, Codex, Pi
- Advisory: Cursor
- Alpha: opencode
- Optional follow-up: local Docker + Ollama workflow smoke

## TOOLS.md row
Insert under **Agent Frameworks & Orchestration** (after asm):

```
| **Statewright** | Agent Frameworks & Orchestration | https://github.com/statewright/statewright | 88 | 70 | 92 | 82 | 85 | A | #agentic #tool-calling #mcp-compatible #local-first #opencode #state-machine #guardrails | **X Entry 056.** Per-phase tool allow-lists via deterministic Rust state machine + MCP gateway. Hard enforcement on Claude Code/Codex/Pi; opencode alpha; Cursor advisory. Self-host Docker Compose; Apache 2.0 engine/agent (gateway FSL→Apache 2029). Pattern layer over Grok CLI / OpenCode — not primary runtime. |
```
