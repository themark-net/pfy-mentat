# AgenC integration notes (reference only)

**Status:** Demoted — [ADR-0010](../../docs/adr/0010-reject-agenc-as-primary-runtime.md).  
Not the primary runtime. Grok CLI + agent-cage are the operator defaults.

This tree may hold **skill/docs extracts** (e.g. loop-engineering) that remain useful as process content independent of the AgenC binary.

## Decision summary

- Tried: install, smoke, `/grok-login`, TUI coding against this repo.  
- Rejected as primary: **UX** (approval TUI), auth confusion, weaker daily loop vs Grok/Claude/OpenCode.  
- Keep: catalog reference; watch web console + marketplace job patterns for possible re-creation.  
- Revisit: only if UX gates in ADR-0010 pass (new ADR).

## Related

- `bootstrap/agenc/` — optional install scripts (not default path)  
- Success path: `make cage-grok-*` + MCP filesystem on workspace + Makefile smokes/versioning  
