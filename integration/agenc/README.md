# AgenC as Primary Runtime + Augmentation Layer

**Status**: AgenC is the official primary runtime for this project (effective 2026-07-12).

This directory contains the integration and augmentation layer on top of AgenC.

## Core Decision

- **Primary runtime**: AgenC (daemon-backed, native OS sandboxing with bubblewrap/Landlock/Seatbelt, MCP client+server, plugin/skill system).
- **High-isolation complement**: agent-cage (full container/VM with network policy) for high-risk or untrusted workloads.
- **No full subtree** of AgenC — we use the official install + runtime update mechanism for maintainability.

## Key Components

- `bootstrap/agenc/agenc-launch` — Primary entry point with update enforcement and offline/caching resilience (`AGENC_OFFLINE=1`).
- `bootstrap/agenc/README.md` — Usage, env vars, and caching guidance.
- `AGENTS.md` — Primary Runtime Policy section (AgenC + agent-cage hybrid).

## Augmentation Layer

Skills, plugins, memory backends, loop patterns, and orchestration logic from this repo are ported here as AgenC-compatible plugins/skills.

### Current Packs

- **loop-engineering/**
  - `4-tier-autonomy.md` — Turn-based, goal-based, time-based, proactive tiers.
  - `14-step-roadmap.md` — Complete progression from manual prompting to production autonomous loops.
  - `plugin-manifest.json` — Pack manifest for AgenC plugin loading.
  - `loop-engineering-plugin-setup.md` — Wiring/registration instructions.

## Resilience Strategy

- Official AgenC install + `agenc runtime update`.
- `agenc-launch` wrapper for on-launch checks and offline mode.
- Future: explicit pinned-artifact cache helper and scheduled background update skill.

## Next Priorities

- Expand loop-engineering pack (goal evaluator, proactive router, scheduled loops).
- Port additional high-value patterns (gstack roles, Graphify-style memory, self-healing docs).
- Build unified skill loader and test harness on top of AgenC.

See `AGENTS.md` for the full policy and `bootstrap/agenc/` for the deployment wrapper.
