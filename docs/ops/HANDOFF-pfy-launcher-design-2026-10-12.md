# Handoff: pfy launcher design (2026-10-12)

Branch: `design/pfy-launcher` (from `main` @ a5c0362). PR: design-only, **do not merge without review**. Not a Feature GO.

## What was done
- Studied morluto/rea (README, `install.sh`, `docs/installation.md`, `src/application/SupportedClients.ts`, `server.json`) and Ollama's `ollama launch` docs.
- Studied pfy-mentat setup surface: AGENTS.md, README, `pfy`/`scripts/pfy`, `pfylib/{cli,toolsets,registry}.py`, `data/{harnesses,toolsets}.json`, `bootstrap/grok-cli/install.sh`, `scripts/pfy_launch_wizard_225.py`, docs/build-dropins.
- Wrote `docs/design/pfy-launcher.md`: rea findings, the `pfy setup` / `pfy launch` / `doctor|update|uninstall` UX, model sources (Grok + Cursor paid; everything else local Ollama/llama.cpp), catalog manifest v2 (extends `data/toolsets.json`), per-harness adapter interface, ownership ledger, safety, rejected alternatives, and phases 1 to 4 with DoD.

## Findings worth knowing
- `pfylib/` cites **ADR-0017** (toolset × harness), but there is no `docs/adr/0017-*.md` and no index row. Someone should write it.
- Skills exist in three copies (`.grok/skills/`, `bootstrap/grok-cli/skills/`, `bootstrap/project-process/skills/`).
- Only Grok is `ready` in `data/harnesses.json`. Claude Code, Codex, Hermes, and OpenCode are `partial`. Cursor CLI is **not listed at all**.

## Next step
Hand **Phase 1** (design §13) to a Grok Build orchestrator run on a fresh worktree (`build/pfy-launcher-p1`). Use fake-HOME tests only: no real harness writes and no network (stub `npx`). Local models only. No sudo.

## Not done
- No code. No ADR filed (proposed as ADR-0018 in the design's §14). No changes to nimo.
