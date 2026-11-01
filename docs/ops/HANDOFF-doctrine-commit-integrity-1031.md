# Handoff: doctrine-commit-integrity-1031

Branch `bot/doctrine-commit-integrity-1031`, base `origin/main` `c0d38af`. Docs and data only. No merge, no PR.

## What landed

- New first-party skill `commit-integrity-and-run-isolation` in `bootstrap/grok-cli/skills/` (SKILL.md, PORT.md), mirrored in `.grok/skills/`.
- Six commit-integrity rules, run-isolation rules, the tester probe checklist, and a rule to commit map for the mvp3 review loop.
- Registered in `bootstrap/grok-cli/manifest.json`, the `bootstrap/grok-cli/README.md` skills table, the `core-skills` bundle in `data/toolsets.json`, and the AGENTS.md portable-skills line.

## Evidence

- `make smoke-grok-skills`: PASS.
- `scripts/catalog_check.py`: PASS.
- `tests.test_pfy_launcher_p1 tests.test_harness2_local_surface tests.test_jev_decision_skill`: 30 OK. Before the `data/toolsets.json` row, `test_v2_items_schema_and_preset` failed because the core-skills bundle did not list the new skill.

## Open

- The commit map cites commits on `bot/mvp3-review-retry`, `bot/mvp-flake-harness2-1031` and `bot/mvp-localbench-tmpdir-1031`. They are not on main yet. Re-check the map when those land.
- `b8ec41d` (pregate Runner.Worker refusal) uses `pgrep -f 'Runner[.]Worker'`. A command line that contains that text, such as a `flock ... bash -c` wrapper that waits for the runner, matches itself. The skill asks for `pgrep -x Runner.Worker`. That fix belongs to the flake-harness2 branch.

## Gate

Docs gate: pregate plus Reviewer. eval-structural dispatched at the tip before the gate.
