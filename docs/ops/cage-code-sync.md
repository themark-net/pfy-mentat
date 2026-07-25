# Cage ↔ host code sync (automated isolation bridge)

**Status:** Active  
**Script:** [harness/agent-cage/scripts/cage-code-sync.sh](../../harness/agent-cage/scripts/cage-code-sync.sh)  
**Run on:** **host** (privileged), not inside the agent container

## Why

| Tree | Role |
|------|------|
| `~/DEVELOP/…/pfy-mentat` (or `local-llm-dev-tools`) | Host catalog git — push to GitHub |
| `~/.agentcage/workspace/pfy-mentat` | Isolated cage workspace (bind-mounted as `/workspace/pfy-mentat`) |

Agents commit **in the cage**. Host `workspace-sync` only rsyncs **host → cage** and used to leave cage-only commits stranded (or risk overwriting them). This tool automates a safe bridge while keeping isolation.

## Commands

```bash
cd ~/DEVELOP/local-llm-dev-tools   # host catalog root

make cage-code-status              # HEADs + divergence
make cage-code-from-cage           # import agent commits → host
make cage-code-to-cage             # rsync host → cage + align cage git tip
make cage-code-sync                # from-cage then to-cage
make cage-code-sync PUSH=1         # also git push origin main
make cage-code-sync FORCE=1        # dirty trees / force align
make cage-code-sync SYNC_ARGS=--dry-run
```

Same via script:

```bash
./harness/agent-cage/scripts/cage-code-sync.sh sync --push
```

## Safe order

```text
1. from-cage   # git fetch cage-ws → merge into host  (never lose agent commits)
2. optional: git push origin
3. to-cage     # rsync content (excludes .git) + reset cage branch to host tip
```

`make cage-code-to-cage` **refuses** if cage has commits not in host (unless `FORCE=1`).

## What is not synced

- `.git` via rsync (history is git fetch/reset only)  
- `.env`, `.grok/sessions`, `.grok/config.toml` (cage MCP preset may re-apply)  
- venvs / node_modules / smoke result noise  

## Recommended loops

| When | Action |
|------|--------|
| After agent work in cage | Host: `make cage-code-sync PUSH=1` |
| Before long host edit session | `make cage-code-from-cage` |
| After host commits | `make cage-code-to-cage` (or full `sync`) |
| Before `workspace-sync` alone | Prefer `cage-code-sync` instead |

Legacy: `make cage-workspace-sync` remains **content-only rsync** (still useful mid-session); prefer **`cage-code-sync`** for end-of-session.

## Env overrides

| Var | Default |
|-----|---------|
| `CATALOG_ROOT` | repo root of this checkout |
| `AGENTCAGE_DIR` | `~/.agentcage` |
| `CAGE_WS` | `$AGENTCAGE_DIR/workspace/pfy-mentat` |
| `SYNC_BRANCH` | `main` |

## Related

- ADR-0011 hybrid surfaces · agent-cage workspace-sync  
- Fracture incident: cage-only commits until host push  
