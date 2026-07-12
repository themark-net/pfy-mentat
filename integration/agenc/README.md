# AgenC as Primary Runtime + Augmentation Layer

**Status:** Primary **host** agent runtime for this project (2026-07-12).  
**Upstream:** [tetsuo-ai/agenc-core](https://github.com/tetsuo-ai/agenc-core) · install [get.agenc.ag](https://get.agenc.ag/install.sh) · npm `@tetsuo-ai/agenc`

This directory is the **augmentation layer** (skills/plugins) on top of AgenC.  
Install + smoke live under [`bootstrap/agenc/`](../../bootstrap/agenc/).

## Core decision

| Runtime | Role |
|---------|------|
| **AgenC** | Primary host coding agent: daemon, TUI/`--print`, MCP, plugins, OS sandbox (bubblewrap/Landlock/Seatbelt) |
| **agent-cage** | High-isolation **container** lab (network policy, untrusted installs, catalog smokes) |

No full subtree of AgenC — use official install + `agenc update`.

## Operator commands

```bash
make agenc-install   # official installer (bootstraps Node 25+ if needed)
make agenc-smoke     # host smoke: launcher offline path + help + daemon

# day-to-day
./bootstrap/agenc/agenc-launch --help
./bootstrap/agenc/agenc-launch daemon status
```

## Key components

- `bootstrap/agenc/agenc-launch` — update + daemon + exec hand-off (`AGENC_OFFLINE=1` supported)
- `bootstrap/agenc/install.sh` — wraps `https://get.agenc.ag/install.sh` (or npm)
- `bootstrap/agenc/smoke.sh` — `make agenc-smoke`
- Skills under `integration/agenc/skills/`

### Current packs

- **loop-engineering/**
  - `14-step-roadmap.md` — progression from manual prompting to autonomous loops  
  - (more pack files may land later: tiers, plugin-manifest)

## Resilience

- Official install + `agenc update`
- `agenc-launch` for on-launch checks and offline mode
- Future: pinned-artifact cache helper / scheduled background update skill

## Related

- Bootstrap README: [bootstrap/agenc/README.md](../../bootstrap/agenc/README.md)
- Cage lab: [harness/agent-cage/](../../harness/agent-cage/)
