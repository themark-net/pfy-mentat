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

## Review fixes (PR 291)
Tester FAIL B1: uninstall treats an empty backup plus a matching sha256 as a file pfy created. It removes the file, or strips only the pfy entry when other content remains, drops those ledger rows, and does not print `sha256 mismatch`. Also locked: never overwrite the first `.pfy.backup`; leave a user-edited skill dir with a warning; a failing `rea setup` (nonzero, or exit 0 with `needs_human` / `needs_confirmation` / `failed`) makes `pfy setup` exit 1; `_run_npx` allowlist is PATH, HOME, temp, XDG_*, npm cache, LANG; one ledger row per shared `~/.agents/skills` path (doctor still reports codex and opencode); delete `.pfy.backup` after a byte-for-byte restore; `plannedActions` / `appliedActions` include files pfy wrote when rea returns `needs_human`; `--harness` without a preset says `nothing was planned`.

## Numbers
- Baseline before the new module: Ran 204 tests, OK (skipped=4). Structural PASS.
- Red-first on base `7702826`, recounted 2026-10-12: `git archive 7702826` plus the original 15-test module from `eb8dd74`. Ran 15 tests in 17.382s, FAILED (failures=12, errors=3). One visible failure is `unknown command: uninstall`. Same 12/3 split as the first red run.
- Review red-first on `eb8dd74` before the engine fix, 11 targeted tests: 8 failed and 3 were already green (`test_first_backup_is_never_overwritten`, `test_uninstall_leaves_user_edited_skill_dir`, nonzero `npx` in `test_failing_rea_setup_exits_nonzero`). The 8 were created-file uninstall, strip-when-other-content, `needs_human` receipt, npx env sentinels, `--harness` without a preset, shared skill rows 30 != 15 (cross-run and inside one four-harness setup), and `.pfy.backup` left after a clean restore.
- Final: `python3 -m unittest tests.test_pfy_launcher_p1` Ran 24 tests in 2.338s, OK. `make eval-structural` PASS. `pfylib_unittests`: Ran 228 tests in 9.339s, OK (skipped=4). 228 = 204 + 24.

## Not in this phase
- `pfy launch`, Cursor, Hermes, update, GUI apply. Phases 2–4 of `docs/design/pfy-launcher.md`.
- ADR-0017 and ADR-0018 are still unwritten. Skill trees were not collapsed.
- `v0.4.17` is the installer pin. `git ls-remote --tags origin` on 2026-10-12 returned no tags, so `v0.4.17` does not exist on origin yet. The one-liner `curl -fsSL https://raw.githubusercontent.com/themark-net/pfy-mentat/v0.4.17/install.sh | sh` and `git clone --branch v0.4.17` need that tag created at release. Dry-run does not fetch. This branch does not create the tag.
- Catalog HOLD 70–75 were not touched.

## Next step
PR 291 is the compare from `build/pfy-launcher-p1` to `main` for #290. Do not merge. Do not tag `v0.4.17` from this branch. Phase 2 starts only after review.
