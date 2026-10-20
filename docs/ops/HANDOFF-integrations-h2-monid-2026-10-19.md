# Handoff: integrations drop-ins for Harness² and local skill discovery (2026-10-19)

- **Branch:** `bot/integrations-h2-monid`, cut from origin/main `a393a91`. Pushed, not merged, no PR (Mark's rule for his own repos). Docs only: two Grok Build drop-ins, two README index rows and this note. No code, no tests, no runs.
- **Why:** Mark set both as HIGH-priority integrations on 2026-10-19, after the catalog entries on `bot/monid-135` (136 Harness², 135 Monid; that branch stays pinned at `2d74fca` for Tester and Reviewer and was not touched).
- **Drop-ins** (Mark pastes them into Grok Build on nimo; each works in its own worktree under `~/DEVELOP/pfy-mentat/tmp/`):

| Order | File | Build branch | What it ships | Loads a model? | Session cap |
|---|---|---|---|---|---|
| H1 | [docs/build-dropins/harness2-local.md](../build-dropins/harness2-local.md) | `build/harness2-local` | Harness² pinned at `1cfe254e8d25` with a local `.env` template (upstream's `.env.example` is missing), a bwrap sandbox whose only network path is a relay to Ollama, a 48-case decision adapter (32/16 split, seed 230), a write allow-list for harness edits, and a proposal writer that pushes only `bot/h2-proposal-*` branches | Yes: `qwen3.6:35b`, quiet host, MemAvailable >= 47 GiB, watchdog at 8 GiB | 6h (live part 3h) |
| H2 | [docs/build-dropins/skill-discovery.md](../build-dropins/skill-discovery.md) | `build/skill-discovery` | Free local discover: pinned fetch of Monid's MIT connector repo (`96e1569dee3a`), our entries and skills, anthropics/skills, cursor/plugins and the official MCP registry into a SQLite index; BM25 then local-model rerank; intake stubs with no entry number; Monid paid runs behind a two-part founder flag and dry-run only; a check that fails if Monid's SKILL.md lands in any skill dir | Short rerank only, after H1 | 4h |

- **Rules both drop-ins carry:** exits written first (STOP file, tries, skips, time cap, red base, memory and busy-host gates), one commit per item, a `RED:` proof per item, a fail/recover test per item, behavior tests only, no sudo or system changes, never stop Mark's processes or unload his models, no paid keys, no secrets, no PR, no merge.
- **Not checked here:** neither drop-in has been run. The runtime estimates in each file come from LOCAL-BENCH-2 (`qwen3.6:35b` 22 GB, about 95 tok/s decode) and the Harness² box demo, not from a nimo run.
- **Open points for Mark:** (1) any Monid account, key or balance stays his call; H2 builds only the off switch. (2) H1's proposal branches need Tester and Reviewer like any other branch; nothing applies a harness edit on its own.
- **Compare:** https://github.com/themark-net/pfy-mentat/compare/main...bot/integrations-h2-monid
