# X intake 2026-10-17: handoff (Entries 128-130)

Daily X intake routine, window 2026-10-17 00:34Z to 2026-10-18 00:36Z (Mark's bookmarks plus the watch list). Three catalog entries at **I0**, one stdlib smoke script with a unit-test file, a folder README paragraph and `.gitignore` lines for receipts. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. #298 (122-124) merged at `c55a58c`; this branch is cut from `main` at `fc6744c` (after #299, #302 and #300), where 127 was the highest entry.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 128 | [Harness Score](https://github.com/paladini/harness-score) (MIT, zero-dep TS, 1.8.2) | Deterministic, offline L0-L4 grade of the harness around a coding agent: AGENTS.md, skills, gate hooks, tests in CI, `.env` and MCP hygiene. **Possible eval-auto trial**: scan our product repos and compare with Tester/Reviewer findings | Yes: Node >= 18 plus a 117 KB tarball under `tmp/`. Smoke PASS on the Grok Bot box |
| 129 | [OpenLore](https://github.com/clay-good/OpenLore) (MIT, TS, 3.3.1) | Local code graph: `orient(task)` for the code a task touches, plus a deterministic breaking-change verdict that names each consumer | Yes, but Node ^22.19 and a ~1.7 GB npm prefix under `tmp/`. Smoke PASS on the Grok Bot box |
| 130 | [hal0](https://github.com/Hal0ai/hal0) (Apache-2.0, v1.4.0) | Inference appliance built first for Strix Halo (ROCm, Vulkan, NPU); published benchmarks on our exact hardware | **Catalog only**: `sudo` installer, `/etc/hal0`, systemd and podman are nimo system changes that need Mark |

Files: `sources/entries/128-harness-score.md`, `129-openlore.md`, `130-hal0.md`, `examples/x-intake-local/smoke_128_130.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py` and `tree_sig` from `smoke_122_124.py` for the fixture check; the real-HOME check uses its own stricter `home_sig`; every child goes through `run_isolated`), `tests/test_x_intake_smoke_128_130.py` (42 stub-based tests), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{harnessscore,openlore}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

Written by the routine through the GitHub connector rather than `./pfy build -p`: docs plus one stdlib script, nimo not needed.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_128_130.py --entry harnessscore|openlore` should exit 2 with an operator reason until staged:

- harnessscore: `mkdir -p ~/DEVELOP/pfy-mentat/tmp/harness-score && cd $_ && curl -LO https://registry.npmjs.org/harness-score/-/harness-score-1.8.2.tgz && tar xzf harness-score-1.8.2.tgz` (sha256 `816c6362704e73111801cfce3861a189c2494868d0a95b4aa7883ca29a0b94c2`). Needs Node >= 18. No `npm install -g`.
- openlore: Node ^22.19 first. If nimo's Node is older, unpack `node-v22.20.0-linux-x64.tar.xz` (sha256 `00bbd05e306ea68b6e13e17360d0e2f680b493ef95f2fea1c4296ff7437530bc`) to `~/DEVELOP/pfy-mentat/tmp/node`. Then `HOME=$(mktemp -d) npm install --prefix ~/DEVELOP/pfy-mentat/tmp/openlore --ignore-scripts --no-audit --no-fund openlore@3.3.1` (temp HOME keeps npm's cache off the real one; the tarball sha256 is `6f810ed71db54a9989b27176fdca0a923676bf2f71a86fe6eb9feb2e119eda90`). About 1.7 GB. Never run `openlore install`, `connect` or `setup`.

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap with no network): harnessscore PASS with Node 20.19.2 and 22.20.0; openlore PASS with Node 22.20.0 and exit 2 with Node 20. Negative paths: missing package dir gives 2; `$HARNESS_SCORE_VERSION=9.9` and `$OPENLORE_VERSION=1.0` give 2; `PFY_XINTAKE_TIMEOUT=0.001` gives exit 1 with "node version timeout after 0.001s". Round 1 (`346d323`): 22 stub tests; Reviewer PASS (full suite 401 OK, `catalog_check.py` PASS, both real runs PASS); Tester FAIL on B1 below.

## Round 2: Tester B1 fix (on top of `346d323`)

- **B1 (blocker): real-HOME check missed permission-only and mtime-only changes**, also on timeout, because it reused `tree_sig` (path, size, content only). OpenLore chmods its token files to 0600, so this mattered.
  - Fix: a local `home_sig()` in `smoke_128_130.py`. Per entry it records path, file type, permission bits and mtime_ns, plus:
    - size and content hash for a readable file;
    - size and inode for an unreadable file;
    - the target string for a symlink (never followed below the watched dir).
  - `tree_sig` and the 122-124 smokes are unchanged.
  - Receipts now list the changed dirs in `real_home_changed`. The reason names only those dirs, also on the normal FAIL path.
- **New tests**, each run for both entries, with a seeded HOME and mtimes restored so only one attribute changes:
  - FAIL: `chmod 600`, `touch -d 2024-05-05`, `chmod 600` plus `PFY_XINTAKE_TIMEOUT=1` (timeout reason plus `real_home_untouched: false`), a symlink swapped to an identical-content target, a nested same-size edit, an empty dir, a rewritten 0000 file;
  - PASS: the seeded HOME left untouched, including the unreadable file.
- **RED**: the new tests are red against `346d323`'s script (12 failures, 7 errors), and green after the fix.
- **Mutants**: drop permission bits, mtime, symlink target, content hash, recursion, dir entries or the unreadable fallback, or revert to `tree_sig`: each turns a test red.
- **Tester F1 (surviving mutants)**: M5, M11, M16, M21, M23, M24, M25, M29 and M31 now each have a killing test.
  - M10 (`tree_sig` `glob` instead of `rglob`) still survives. It is equivalent here: `tree_sig` now only guards the flat fixtures, and a nested write still adds a top-level dir line. The `home_sig` version of that mutant (H4) is killed.
- **Tester F2**: Harness Score's PASS reason now names its watched dirs, as OpenLore's does. Scope is stated: writes outside the watched dirs (e.g. `~/.newdot`) are not watched.
- **Tester F4 (catalog)**: Harness Score 585 stars; OpenLore install added 322 packages (lockfile 393); hal0 model `qwen3.6-35b-a3b-crown`.
- **Reviewer nit**: if the run raises (e.g. a timeout before any check), `checks.body_completed` is false and `exception` names it. `main()` still writes the FAIL reason.
- **Runs (nimo worktree)**: 42 stub tests OK. Full suite: `Ran 421 tests`, `OK (skipped=4)`. `catalog_check.py`, `smoke_contract_lint.py` and `check_no_encoded_payloads.py` all PASS.
- **Real tools, new script (Grok Bot box, bwrap, temp HOME seeded with `~/.openlore/tok` at 0600 and `~/.harness-score/c`)**: Harness Score 1.8.2 PASS on Node 20.19.2; OpenLore 3.3.1 PASS on Node 22.20.0. Both show `real_home_untouched: true`, so there is no false FAIL.

## Findings worth knowing

- **OpenLore's `analyze` exits 0 when its index build panics** (LanceDB panics on a read-only `/tmp`); `orient` then reports "No analysis found". Judge it by `orient`/`status` output and keep `TMPDIR` writable.
- **OpenLore checks registry.npmjs.org for updates by default** and caches in `~/.openlore/`; set `OPENLORE_NO_UPDATE_NOTIFIER=1`. Telemetry is opt-in. `install`/`connect`/`setup` write host agent configs, a SessionStart hook and `~/.pi/agent/extensions`.
- **Harness Score keeps a short but real AGENTS.md at L0** (CTX-02 wants more substance), and it reads ignored files, so a local `.env` fails HYG-03 on a dev checkout. Read named checks, not just the level.
- **hal0 ships with auth off** (LAN-open) plus an unauthenticated OpenWebUI listener on `:3001`, and wants `:8080`.

## Recommended next steps (not started)

1. **Eval-auto trial: Harness Score across our repos.** On nimo, scan clean worktrees of pfy-mentat, leasegrid-c, quietsoap and product-site-template with `--json`. For each failed check, note whether Tester or Reviewer caught the same class of problem on a recent PR (secret leak, missing gate hook, tests not in CI). If the hygiene and hooks checks match real misses, add them as an advisory G0 step with a `.harness-score.json` that switches off Cursor-only checks with reasons.
2. OpenLore vs codebase-memory-mcp: same 5 Build-sized tasks on pfy-mentat, compare `orient` hits and tokens read; run `certify-public-surface --base main` on the next two Python PRs before Tester and compare with what Tester finds.
3. hal0: only if Mark wants a packaged runtime. Otherwise use its leaderboard as a reference when re-benchmarking after a ROCm 7.2 userspace upgrade.

## LATER (logged, not cataloged this run)

- **ForgeDock** (@DanKornas, AGPL-3.0, JS). Issue-in, PR-out pipeline for Claude Code and OpenCode with GitHub as the durable record. Closest to our missing unattended implement loop; AGPL, compare with `/one-shot` before anything else.
- **SACP** (@DanKornas, MIT, Python). Text-first protocol for auditable work receipts on long agent runs. Overlaps Entry 124 (Squadra) proof-before-close.
- **showagent** (@DanKornas, MIT, Go). Local picker that moves a session between coding-agent CLIs (OpenCode among them). Useful if pfy switches harnesses mid-task; Grok CLI not listed.
- **Evolving Agents** (@DanKornas, Apache-2.0). Director agent that learns team rules from CLAUDE.md and memory. Overlaps Entry 119 (AgentDescent).
- **llm-wiki-compiler** (@DanKornas, MIT, 2.2k stars). Karpathy-style LLM Wiki compiler with citations; needs a model endpoint to compile, would need a local one.
- **KiwiFS** (@DanKornas, license unclear). Markdown filesystem knowledge base for agents and teams.
- **DeepGym** (@DanKornas, license unclear). RL environments with verifiable rewards for coding and computer-use agents; eval reference.
- **Coordinate Agents**, **JarvisCore**, **gptme-agent-template**, **Brenner Bot** (@DanKornas). Multi-agent coordination and agent templates overlapping Squadra and the orchestrator loop.
- **camoufox-cli** (@DanKornas). Overlaps Entry 071 (camofox-browser).
- New DeepSeek model at 77 on DeepSWE (@aisearchio quoting @deepseek_ai). Check size and open weights before a local-bench slot.
- @tom_doerr's Stealth Browser MCP left to Mark's weekly tom_doerr automation (and it's a bot-check bypass, not something we want).

TRADING (parked desks, no action): Simmer SDK (prediction-market SDK, MCP and skills), @ch3nweiii's trading-agent prompt.

SKIPPED: open-computer-use (linked repo not reachable), Keepresso and Harness terminal (macOS), MailCheap, GetVect, Bria AI Skills (needs a Bria key), spel (Clojure Playwright), ROS2 MCP, lampOS, Pluto (Salesforce), MSP Skills, Marketing Skills (already in sources), AI System Design guide, the AI engineering master tree, Vibelution and GuideAnts (workbenches), @yume_arasaki's RED-SNOW recipe (two DGX Sparks, NVIDIA), @alex_verem's free-apps list (PhotoCraft, WordCraft, anarlog, VoiceStudio; OpenCode already cataloged), science and opinion posts, Nebula promos, and replies. Bookmarks: the vibe-coder security checklist is covered by the dev-skills slice on main (Entries 125-127, #302); the copy-principle post is marketing.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector). No accounts, sign-ins, paid keys or spend. Harness Score and OpenLore ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model or agent CLI was started. Round 2 was done in a temporary nimo worktree under `tmp/`, removed afterwards; stub tests only on nimo, nothing installed.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 128-130 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| A tool writes to the real HOME | `~/.openlore` or `~/.harness-score` appears or changes on nimo | Both smokes fingerprint the watched dirs (`home_sig`: content, size, type, permissions, mtime, symlink target) before the run and in a finally, and FAIL on any change, also on timeout. Writes outside the watched dirs are not seen |
| `smoke_122_124.tree_sig` changes | Import breaks (fixture check only) | The tests import the smoke end to end; move `tree_sig` into `smoke.py` if it's reused again |
