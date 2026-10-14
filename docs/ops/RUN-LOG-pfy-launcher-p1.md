# Run log: pfy-launcher-p1

Slug: pfy-launcher-p1
Branch: build/pfy-launcher-p1
Worktree: /home/mark/DEVELOP/pfy-mentat/tmp/pfy-launcher-p1
Issue: #290 = design §13 Phase 1
Base: 7702826 (origin/main at fetch)
Baseline (before new tests): `python3 -m unittest discover -s tests -t .` → Ran 204 tests, OK (skipped=4). `make eval-structural` → STRUCTURAL EVAL: PASS.

Overview: Phase 1 of docs/design/pfy-launcher.md lands a root-refusing, tag-pinned install.sh, v2 catalog fields on data/toolsets.json for core-skills, code-graph, and delegated rea, four setup-only adapters, and pfylib setup/doctor/uninstall with a ledger. Behavior tests in tests/test_pfy_launcher_p1.py use a temp HOME and a fake npx. Gate nits on the design doc are fixed in the same branch. No network, no model loads, no sudo, HOLD 70–75 untouched.

Phases:
- tests-red | tests/test_pfy_launcher_p1.py | unittest of that module fails on current tree | none | lead
- catalog | data/toolsets.json, data/schema/catalog-item.v2.json, scripts/catalog_item_validate.py, examples/eval-harness/run_structural.py (one check) | CatalogTests pass; registry.validate empty; catalog_check still PASS | tests-red | general
- install | install.sh | InstallTests pass | tests-red | general
- docs-nits | docs/design/pfy-launcher.md, docs/ops/HANDOFF-pfy-launcher-design-2026-10-12.md | stubs/partial wording, ADR-0012 filename plus duplicate number, merge_config path, one project-map line | none | general
- engine | pfylib/adapters/, pfylib/setup.py, pfylib/cli.py, pfylib/__init__.py, scripts/pfy | SetupTests and SecretTests pass; bare pfy help still exit 0 | tests-red | general
- handoff | docs/ops/HANDOFF-pfy-launcher-p1-2026-10-12.md, docs/TODO.md, commit, push, one PR | make eval-structural PASS; final test count recorded; PR open or compare URL written | all above | lead

Risks:
- Misrouting `pfy setup` into cmd_setup runs `make env-init` and can edit `.env`. Mitigation: catalog flags dispatch before cmd_setup; agents must not run bare `pfy setup`.
- Shared worktree. Mitigation: disjoint paths; nobody edits tests/test_pfy_launcher_p1.py; lead commits once.
- New toolset rows marked implemented would fail test_toolsets.py (no planner). Mitigation: decision 7, stub cells.
- No GitHub release tag. Mitigation: decision 2, dry-run does not fetch.
- gh unauthenticated. Mitigation: decision 12.

## tests-red
state: DONE | tests: python3 -m unittest tests.test_pfy_launcher_p1 → Ran 15 tests, FAILED (failures=12, errors=3) on the pre-fix tree | files: 1 | err: install.sh missing, catalog v2 fields missing, pfy uninstall unknown
Workstreams spawned: catalog 01a1330e-c172-7f70-9591-faa3ceb58f82, install 01a1330e-c172-7f70-9591-facb3010f6ba, docs 01a1330e-c172-7f70-9591-fadf5c05e5d1, engine 01a1330e-c172-7f70-9591-faea33426cc3, map 01a1330e-c172-7f70-9591-faf359b067af.

## catalog
state: DONE | tests: CatalogTests OK; catalog_item_validate PASS; catalog_check PASS (toolsets=8). test_registry seeded-id set updated by the lead to include core-skills and rea | files: 4 | err: none

## install
state: DONE | tests: InstallTests Ran 4 OK | files: 1 | err: none

## docs-nits
state: DONE | tests: lead applied the four wording edits after the spawned agent wrote a project map instead of the design | files: 2 | err: none

## map
state: DONE | tests: .project-map/index.html written | files: .project-map only | err: none

## engine
state: DONE | tests: SetupTests+SecretTests OK; full module inside make eval-structural | files: adapters, setup.py, cli.py, scripts/pfy | err: none

## loop-paint
state: DONE | tests: test_loop_paint stub set is core-skills and rea; make eval-structural PASS (219 tests) | files: tests/test_loop_paint.py | err: first structural run failed that assertion once

## handoff
state: DONE | tests: make eval-structural PASS · Ran 219 OK (skipped=4) · baseline was 204 | files: HANDOFF, TODO, this log | err: none

## review-291
state: DONE | tests: base recount on 7702826 Ran 15 in 17.382s FAILED (failures=12, errors=3); launcher module Ran 24 in 2.338s OK; make eval-structural PASS; pfylib_unittests Ran 228 in 9.339s OK (skipped=4) | files: pfylib/adapters/base.py, pfylib/setup.py, tests/test_pfy_launcher_p1.py, docs/design/pfy-launcher.md, HANDOFF, decisions 14–22 | err: none. v0.4.17 still absent on origin. Do not tag. Do not merge.
