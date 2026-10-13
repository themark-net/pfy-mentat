# Handoff: pfy launcher phase 1 (2026-10-12)

Branch: `build/pfy-launcher-p1`. Issue #290. Not a Feature GO. Do not merge from this handoff.

## What landed
- `install.sh`: `{…}` guard, `--dry-run` / `--version` / `--no-setup`, root refusal unless `PFY_ALLOW_ROOT=1`, pin `v0.4.17` (not `main`). Dry-run prints the plan and writes nothing.
- Catalog v2 on `data/toolsets.json`: `core-skills` (bundle copied from `bootstrap/grok-cli/skills/`), `code-graph` (native MCP `codebase-memory-mcp`), `rea` (delegate `npx -y rea-agents@6.4.0 setup --client …`). Schema `data/schema/catalog-item.v2.json`. `scripts/catalog_item_validate.py` is a structural check.
- `pfylib/setup.py` plus adapters `pfylib/adapters/{grok,claude_code,codex,opencode}.py`. `pfy setup` with catalog flags, read-only `pfy doctor --json`, ledger uninstall under `$XDG_STATE_HOME/pfy/installed.json`.
- Bare `pfy setup [profile]` and bare `pfy doctor` are unchanged.
- Design gate nits: Gemini/Exo/Continue are `partial` in `data/harnesses.json` and `stub` in the toolset matrix; ADR-0012 is cited as `0012-simple-harness-agnostic-launch.md` (the voice ADR reuses the number); `merge_config.py` is `bootstrap/grok-cli/scripts/merge_config.py`.
- The project-map subagent writes `.project-map/index.html` and does not write other project files.

## Commands
```bash
python3 -m unittest tests.test_pfy_launcher_p1 -v
make eval-structural
```
Tests use a temp `HOME` and a fake `npx`. No network.

## Numbers
- Baseline before the new module: Ran 204 tests, OK (skipped=4). Structural PASS.
- New module on the pre-fix tree: Ran 15 tests, FAILED (failures=12, errors=3).
- Final: `make eval-structural` PASS. `pfylib_unittests`: Ran 219 tests in 8.101s, OK (skipped=4). 219 = 204 + 15.

## Not in this phase
- `pfy launch`, Cursor, Hermes, update, GUI apply. Phases 2–4 of `docs/design/pfy-launcher.md`.
- ADR-0017 and ADR-0018 are still unwritten. Skill trees were not collapsed.
- `v0.4.17` is the installer pin. Origin has no git tag yet, so a real clone fails until that tag exists. Dry-run does not fetch.
- Catalog HOLD 70–75 were not touched.

## Next step
Open one PR from `build/pfy-launcher-p1` to `main` referencing #290. Do not merge. Phase 2 starts only after that review.
