# X intake 2026-10-27: handoff (Entry 148)

Daily X intake routine, window 2026-10-27T00:40Z to 2026-10-28T00:40Z. Sources: Mark's 40 latest bookmarks (2 new, both off-core) and the watch-list posts (4 pages, mostly @DanKornas repo posts). One catalog entry at **I0**, one stdlib smoke script with a unit-test file and a `.gitignore` line for its receipt. Catalog-only; not a Feature GO and nothing here competes with the pfy-mentat MVP. Catalog HOLD 70-75 untouched. Branch cut from `main` at `2f2b20e` (highest entry 147).

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 148 | [SkillSpector](https://github.com/NVIDIA/SkillSpector) (Apache-2.0, v2.12.0) | Static, offline security scanner for agent skills with a SAFE / DO_NOT_INSTALL verdict and exit code: the install gate H2 skill discovery lacks. **Eval-auto trial candidate** | Expected yes (pure Python, CPU). Smoke PASS on the box; not staged on nimo yet (smoke exits 2 there until it is) |

Files: `sources/entries/148-skillspector.md`, `examples/x-intake-local/smoke_148.py` (self-contained, stdlib only), `tests/test_x_intake_smoke_148.py` (10 stub tests), `.gitignore` line for `pipelines/smoke/skillspector/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows. Written on the Grok Bot box and pushed through the GitHub connector (docs plus one stdlib script). No PR, per Mark's 2026-10-19 rule: gate this branch at its pinned head, then fast-forward `main`.

## How to gate

```sh
python3 -m unittest tests.test_x_intake_smoke_148   # 10 tests, no SkillSpector needed
python3 examples/x-intake-local/smoke_148.py         # exit 2 unless staged; PASS when staged
python3 scripts/catalog_check.py
```

To stage on nimo (inside DEVELOP only): `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/skillspector/.venv && ~/DEVELOP/pfy-mentat/tmp/skillspector/.venv/bin/pip install git+https://github.com/NVIDIA/SkillSpector.git@e7172462caf367736645f66c1aa154ca5f9c64dc`, then rerun the smoke.

Checked on the box: smoke PASS (benign fixture SAFE score 0 exit 0; malicious fixture DO_NOT_INSTALL score 93 exit 1 with P1, SC2, TM2, PE3; temp HOME empty; real-HOME paths unchanged; bwrap with no network). Unit tests 10 OK. `scripts/catalog_check.py` not run on the box for this branch.

## Triaged and skipped this run

- Tingly Box (tingly-dev/tingly-box, MPL-2.0): agent-to-model gateway with routing. Overlaps HiRoute (147) and HarnessRouter (123), which already cover the comparison.
- uzu (Metal inference engine, "4x llama.cpp"): Apple-only, no AMD path.
- senpi (pi-mono fork), Local Operator, MoAI-ADK, LemonClaw, Pinchy (OpenClaw-based), NAISYS, WOML, 0 (security harness), awesome lists for agent memory and computer-use agents: either Claude-Code-specific, OpenClaw-based (Hermes is the chosen interface), lists rather than tools, or not ahead of what pfy-mentat already has.
- Bookmarks: startup credits list and an options-selling post (trading, log only, no action; trading work is suspended).

## Recommended next step (after the MVP)

Stage SkillSpector on nimo and run `scan --no-llm` over every skill already imported through intake (`bootstrap/grok-cli/skills/`, Hermes skills) to size the false-positive rate, then wire it as a pre-install check in the H2 discovery path.
