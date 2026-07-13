# Session brief — import into cage / Grok

**Date:** 2026-07-12  
**Repo:** pfy-mentat (`/workspace/pfy-mentat` in cage)  
**Use:** Paste into `grok` as first message, or keep as operator notes.

---

## One-line

We demoted AgenC, made Grok Build the cage operator path with filesystem MCP on the catalog tree, and next we need **persisted, repo-isolated Grok sessions** inside the cage.

## What shipped this session

| Item | Status | Notes |
|------|--------|-------|
| OQ-0002 eval harness option 5 + v0.2 suite/matrix | done | `make eval-mvp` / `eval-v02` / `eval-matrix` |
| OQ-0005 Grok dual-path (host + in-image) | answered | |
| AgenC trial + install/smoke | demoted | **ADR-0010** — TUI/UX unfit vs Grok/Claude/OpenCode |
| Uninstall AgenC host | done | No make targets; **T-0046** re-eval later |
| T-0045 Grok + workspace + filesystem MCP | done | `make cage-grok-ready` green |
| Launch UX | done | `make cage-grok` → `cage-grok-shell` / `cage-grok-run` |
| Init idempotency | improved | `cage-init` skips if project exists |

## Architecture (current)

- **Primary operator:** Grok Build CLI (ADR-0002)  
- **Isolation lab:** agent-cage (MCP filesystem on `/workspace`)  
- **Not primary:** AgenC (ADR-0010)  
- **Catalog tree in cage:** `/workspace/pfy-mentat` via `make cage-workspace-sync`  
- **Grok MCP:** project `.grok/config.toml` → `http://172.30.0.10:8096/servers/filesystem/mcp`  
- **Auth:** host `grok login` → `make cage-grok-auth-import` → mount `auth.json` only  

## How to launch (operator)

```bash
make cage-grok              # ensure up + sync + ready
make cage-grok-run          # interactive Grok in catalog tree
# or
make cage-grok-shell        # then: grok / grok -c
```

## Gaps / next work

1. **T-0047 — Session resumption design** (see `cage-session-resumption-design.md`):  
   - Persist `$GROK_HOME/sessions` on host under `~/.agentcage/grok-state/sessions`  
   - Mount into cage; resume with `grok -c` / `-r` per stable repo cwd  
   - Isolate by repo path / repo_id  

2. **T-0042** catalog re-score (parked)  
3. **T-0043** write-guard mcp-host wiring (optional)  
4. **T-0046** AgenC re-eval when UX gates pass  
5. Local Ollama as Grok model backend still a **separate** path (`local-ollama-up`)  

## Can Grok call local agents?

- **Filesystem MCP:** yes (cage workspace)  
- **Grok subagents / built-in tools:** yes (in-process)  
- **Ollama via LiteLLM:** separate make path, not default Grok overlay  
- **AgenC marketplace jobs:** no (demoted)  

## Open decisions

- Multi-repo layout: keep `/workspace/pfy-mentat` only vs `/workspace/repos/<id>`  
- Whether to ever import **host** session transcripts into cage (different cwd keys)  

## Suggested first prompt in cage after resume feature

> Continue T-0047: implement grok-state sessions volume + `make cage-grok-resume` per docs/ops/cage-session-resumption-design.md. Do not reintroduce AgenC. Keep ADR-0002.
