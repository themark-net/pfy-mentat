### Entry 056: Statewright — State Machine Guardrails for AI Agent Tool Use

- **URL**: https://x.com/i/status/2084511054877380691
- **Date**: 2026-08-04
- **Poster**: Tom Dörr (@tom_doerr)
- **Summary / Key Claims**: Statewright enforces which tools an AI agent may call in each workflow phase via a deterministic state machine (“Agents are suggestions, states are laws”). Define a workflow once; reject out-of-phase tool calls across Claude Code, Codex, Cursor (advisory), opencode (alpha), and Pi. Self-hostable Rust engine + MCP gateway + optional managed cloud. Directly addresses agent reliability (no deploy tools during planning).
- **Extracted Repos / Tools**: Primary: https://github.com/statewright/statewright — Rust engine, sw-agent binary, MCP gateway, visual workflow editor, Docker Compose self-host.
- **TOOLS.md Link**: New row under Agent Frameworks & Orchestration (initial scores: S1=88 S2=70 S3=92 S4=82 overall ~85 tier A).
- **Notes**: Strong fit for local-first agent discipline and OpenCode/Ollama path. Stage 0 pass. opencode support still alpha. Not a primary runtime — pattern + optional guard layer over Grok CLI / OpenCode / agent-cage.
- **Status**: Quick-evaluated - cataloged (initial scores; A / I1)
