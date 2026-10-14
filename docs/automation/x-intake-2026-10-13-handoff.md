# X intake 2026-10-13: handoff (Entries 115-116)

Daily X intake routine, window 2026-10-13 00:40Z to 2026-10-14 00:39Z (Mark's bookmarks plus the watch list). Two catalog entries at **I0** plus one stdlib smoke script. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. Previous slice: #292 (Entries 112-114), open and in gates when this branch was cut from `main` (highest entry on `main`: 111). The two PRs touch different files, so either can merge first.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 115 | [OpenQodex](https://github.com/openqodex/openqodex) (Apache-2.0, npm 0.12.0) | Pre-push review: scanners on changed lines, then a reviewer that must raise or drop every finding, checked by a model-free `--finalize`. `review --agent` lets any agent be the reviewer. **Eval-auto candidate** as the Reviewer's first pass vs today's hand review of the diff | Yes, package plus Node 22 under `tmp/openqodex`, `HOME` under `tmp/`. Never `init`. Smoke PASSed on the Grok Bot box |
| 116 | [assay](https://github.com/awss1i/assay) (MIT, PyPI `assay-ui` 0.3.0) | Deterministic, no-LLM web-page QA: opens the page in Chromium and uses every control. A cheap pre-check before Tester's launch check on GUI PRs | Yes, venv and Chromium under `tmp/assay`. Smoke PASSed on the box under a read-only root with no network |

Files: `sources/entries/115-openqodex.md`, `116-assay.md`, `examples/x-intake-local/smoke_115_116.py` (imports `TMP` and `write` from `smoke.py`; other smoke scripts unchanged), and this handoff. The folder README is not edited here, to avoid a conflict with #292's README paragraph; the script's docstring documents its env vars. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target, no `.gitignore` change. Box receipts are not committed.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_115_116.py --entry openqodex|assay` should exit 2 with an operator reason until staged under `~/DEVELOP/pfy-mentat/tmp`:

- openqodex: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/openqodex --ignore-scripts openqodex@0.12.0`, plus Node 22 at `tmp/openqodex/node/` (nodejs.org `latest-v22.x` linux-x64 `.tar.gz`, checked against `SHASUMS256.txt`) if nimo's Node is older. The first smoke run downloads scanners into `tmp/openqodex/home` (about 360 MB, network needed once).
- assay: `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/assay/venv && ~/DEVELOP/pfy-mentat/tmp/assay/venv/bin/pip install assay-ui==0.3.0`, then `PLAYWRIGHT_BROWSERS_PATH=~/DEVELOP/pfy-mentat/tmp/assay/ms-playwright ~/DEVELOP/pfy-mentat/tmp/assay/venv/bin/playwright install chromium` (about 690 MB).

Or point `$OPENQODEX_DIR`/`$OPENQODEX_NODE`/`$OPENQODEX_HOME` and `$ASSAY_BIN`/`$PLAYWRIGHT_BROWSERS_PATH` at staged copies. Receipts go to `pipelines/smoke/<entry>/latest.json`.

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs): both PASS. Negative paths: no prereqs gives exit 2 for each; Node 20 gives 2 (openqodex); `$OPENQODEX_VERSION=9.9.9` gives 2; `$ASSAY_VERSION=9.9.9` gives 2; a `PLAYWRIGHT_BROWSERS_PATH` with no Chromium gives 2; `PFY_XINTAKE_TIMEOUT=0.001` gives exit 1 with a timeout reason. The box's real `~/.openqodex` and `~/.claude` did not exist afterwards. `python3 -m py_compile` is clean. The repo's `scripts/catalog_check.py` and unit tests were not run in this slice (no checkout on the box); Tester should run them on the PR head.

## Findings worth knowing

- **OpenQodex is warn-only by default**: a finalize with one major security finding printed "Passed with warnings: 1 finding (1 major)" and exited 0. A gate must set a block threshold in `.openqodex/config.yaml` or read the receipt.
- **OpenQodex writes into the repo on a plain `review`**: `.openqodex/config.yaml`, `custom-instructions.md` and `reviews/`. Only run it in a throwaway worktree until we decide to adopt it.
- **OpenQodex refuses Cursor as reviewer** ("cursor-agent cannot be limited to reading") and lists only Claude Code or Codex, which we don't have. `review --agent` is the path that works for us: the agent we already run follows the brief, and `--finalize` checks its answer without a model.
- **assay misses silent no-ops**: a button that does nothing passed all three checks. A thrown error is caught and grouped. It needs a writable `TMPDIR` under a read-only root.

## Recommended next steps (not started)

1. **Eval-auto trial: OpenQodex `review --agent` + `--finalize` as Reviewer's first pass** on the next three pfy-mentat PRs, in a throwaway worktree under `tmp/`, with Grok Build or the Reviewer bot following the brief. Compare against the hand review on the same heads: real issues found, false positives dropped with reasons, time taken. Set a block threshold first.
2. assay: run it on the pfy-mentat GUI's built pages next to Tester's launch check on one GUI PR, and note what each catches.

## LATER (logged, not cataloged this run)

- **UFO** — https://github.com/ufo-ai/ufo-core (Apache-2.0). Self-hosted team agent runtime; needs three model API keys we don't have.
- **Marvis** — https://github.com/marvis-ai/marvis (Apache-2.0). Desktop co-pilot over screen and meetings; off our pipeline.
- **Altprobe** — https://github.com/olegzhr/altprobe (Apache-2.0). Collector/correlator for agent, MCP and gateway traffic; security ops, low fit now.
- Matt Pocock's list of agent-workflow mistakes (skills too long, effort too high, aligning too often, lax automated checks) and his note that skill evals are harder than classifier evals: technique notes for our skills and best-effort doctrine, no artifact.
- @_avichawla on VRAM: weights are one of four allocations, so a model can load and still run out of memory on the first requests. Matches our nimo lockup notes; no artifact.

SKIPPED: Colibri (already cataloged, Entry 003 and TOOLS.md), Asqav SDK and Clisbot (license NOASSERTION), Rojo Compass (Roblox), Seekter (job search), ux-ui-agent-skills (Claude-only design prompt), ESP32 multi-protocol tool (hardware), Iris 3B Turbo (image model, off scope), the Karpathy paper-lab thread (no artifact), replies and newsletter posts. No new bookmarks since the last run.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector and raw URLs). No accounts, sign-ins, paid keys or spend. Tools ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model was called. No installer scripts were run (`npm --ignore-scripts`; OpenQodex `init` not run).

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 115-116 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| OpenQodex starts a model | `claude` or `codex` appears on PATH | Smoke exits 2 before running when either is on its PATH |
| Large downloads | Scanners and Chromium fill `tmp/` | Both stay under `tmp/`; delete the folders to reclaim |
