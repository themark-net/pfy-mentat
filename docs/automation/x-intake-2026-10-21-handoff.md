# X intake 2026-10-21: handoff (Entries 140-142)

Daily X intake routine, window 2026-10-21T00:39Z to 2026-10-22T00:37Z. Sources: 157 watch-list posts (7 pages; page 8 empty), including one @tom_doerr post. **Bookmarks were not read this run**: the X connector needs re-auth, so Mark's latest bookmarks will be diffed on the next run that has access. Three catalog entries at **I0**, one stdlib smoke script with a unit-test file, a folder README paragraph and `.gitignore` lines for receipts. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. 137-139 are on `main`; this branch is cut from `main` at `7281cd1` (highest entry 139), so numbering continues at 140.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 140 | [Chiasmus](https://github.com/yogthos/chiasmus) (Apache-2.0, TypeScript, 0.1.40) | MCP server with Z3, Prolog and tree-sitter call graphs: Reviewer/Tester and the decision layer can ask a solver about rules, dependencies, reachability and blast radius instead of guessing. No key needed. **Possible eval-auto trial for Reviewer** | Yes: 180 MB npm prefix under `tmp/`, Node 22+, CPU only. Smoke PASS on the Grok Bot box |
| 141 | [Tracekit](https://github.com/Cygnux-Labs/Tracekit) (MIT, Python, `tracekit-ai` 1.4.1) | Policy gate before each tool call plus signed, offline-verifiable run bundles: tamper-evident receipts for gated runs. Sits between Sandlock (096, kernel confinement) and neatroots (137, post-hoc trace rules). **Possible eval-auto trial on gate receipts** | Yes: 44 MB venv under `tmp/`. Smoke PASS on the box (dev signer, policy, approvals, verify and three tamper cases) |
| 142 | [Charlotte](https://github.com/TickTockBent/charlotte) (MIT, TypeScript, 0.8.0) | Browser MCP server that returns structured pages at three detail levels with stable element ids and a 7-tool `core` profile: browsing within a small local-model context | Yes with a browser: 85 MB npm prefix plus Chrome/Chromium under `tmp/`. Smoke PASS on the box |

Files: `sources/entries/140-chiasmus.md`, `141-tracekit.md`, `142-charlotte.md`, `examples/x-intake-local/smoke_140_142.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py` and `home_sig`, `finish`, `as_json`, `pkg_version`, `tmo` from `smoke_128_130.py`; every child goes through `run_isolated`; the real-HOME paths are fingerprinted with `home_sig` before the run and in a finally), `tests/test_x_intake_smoke_140_142.py` (76 stub-based tests), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{chiasmus,tracekit,charlotte}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

Written by the routine through the GitHub connector rather than `./pfy build -p`: docs plus one stdlib script, nimo not needed. Pushed as a branch with no PR (Mark's 2026-10-19 rule): gate this branch at its pinned head, then fast-forward `main`.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_140_142.py --entry chiasmus|tracekit|charlotte` should exit 2 with an operator reason until staged:

- chiasmus: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/chiasmus --ignore-scripts --omit=optional --no-audit --no-fund chiasmus@0.1.40` (tarball sha256 `0d1e911a8ada5007c5f440d0c87a0f284d367188aeb2d0f8fba790f833500a34`). If nimo's `node` is older than 22, unpack `node-v24.14.1-linux-x64.tar.xz` from nodejs.org into `tmp/chiasmus/node` (strip the top dir). Never `npm install -g` or `claude mcp add`.
- tracekit: `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/tracekit/venv && ~/DEVELOP/pfy-mentat/tmp/tracekit/venv/bin/pip install tracekit-ai==1.4.1` (wheel sha256 `2166ceba02d451cdca52c922617e0c5b14c44936efeaf3c651cec89dfcf2aa60`; the package is `tracekit-ai`, not `tracekit`). Never `tracekit init`, `up` or `uvx`.
- charlotte: `PUPPETEER_SKIP_DOWNLOAD=1 npm install --prefix ~/DEVELOP/pfy-mentat/tmp/charlotte --no-audit --no-fund @ticktockbent/charlotte@0.8.0` (tarball sha256 `b6a94defc8ea1d42cf5e89110cf32d77c22cd5fa7fb992db23621e04ec333eec`). Browser: an installed `chromium`/`google-chrome` is picked up; otherwise `cd ~/DEVELOP/pfy-mentat/tmp/charlotte && npx @puppeteer/browsers install chrome@148.0.7778.97 --path browsers && mkdir -p chrome && ln -s "$PWD"/browsers/chrome/linux-148.0.7778.97/chrome-linux64/chrome chrome/chrome`. Never `npm install -g`, and never install without `PUPPETEER_SKIP_DOWNLOAD=1` (it writes `~/.cache/puppeteer`).

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored; `$PFY_SMOKE_RECEIPT_DIR` overrides).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap 0.12.0 with no network):

- **chiasmus PASS** (0.1.40, Node 24.14.1): 9 tools over stdio; Z3 unsat core `[gt10, lt5]` and a sat model `x = 11`; Prolog proves `reach(a,c)` and finds no `reach(c,a)`; on a 2-file Python fixture `unused_helper` is dead code, `handle` reaches `connect` and `unused_helper` doesn't, `impact(connect) = [query, handle]`; lint catches an unclosed parenthesis; starter templates found; skill DB only in the temp `CHIASMUS_HOME`.
- **tracekit PASS** (1.4.1): dev signer in the temp dir; `ls`/`git status` allowed, `sudo rm -rf /` and `curl | sh` denied, an unparsable command held and its approval bound to the approved arguments (a swap refused and signed as `approval.binding_mismatch`); `tracekit verify` exit 0 VERIFIED; a re-hashed copy with the denial flipped fails `signatures`, one with a record dropped fails `run chain`, and a foreign witness fails `witness quorum`.
- **charlotte PASS** (0.8.0, Node 24.14.1, Google Chrome 155): `core` profile, 7 tools; on a `file://` form, minimal navigate (724 bytes, no ids, no body text), observe lists the input and button, find returns the same id, type and click run the page's submit and `full` shows the result; ids stable; an unknown id is an error and the server keeps going; clean shutdown with no profile left.
- Negative paths: wrong pins (`CHIASMUS_VERSION=0.1.39`, `TRACEKIT_VERSION=1.4.0`, `CHARLOTTE_VERSION=0.7.0`), missing packages, and Node 20 for Chiasmus each give 2.
- Unit tests: 60/60 OK in about 56 s at the first push; 76/76 OK in about 60 s on nimo after the Tester fix below (fake `node` MCP servers for Chiasmus and Charlotte, a fake venv and `tracekit` package for Tracekit). Each of the 46 checks the smoke records has a test that turns it false: the 44 per-entry checks each through a stub knob, `driver_report` included for all three entries (a Chiasmus server that exits mid-run, a Tracekit driver whose export raises, a Charlotte server that exits on a bad id), and `body_completed` and `real_home_untouched` through the timeout and real-HOME plant tests. Also covered: temp-HOME writes, real-HOME writes without bwrap for the watched paths, a real-HOME change during an early exit 2 (turns it into a FAIL), a server that ignores SIGTERM, timeouts that keep the real-HOME check, and exit 2 for a missing Chrome, a bad `$CHIASMUS_NODE`, `$CHARLOTTE_NODE` or `$CHARLOTTE_CHROME`, and a `PFY_XINTAKE_TIMEOUT` that is not a number > 0. Crashing-server tests exist for Chiasmus and Charlotte only; Tracekit has no server process (its driver error is the equivalent). Five hand mutants of the smoke (Chiasmus Node floor, Tracekit witness-quorum check, Charlotte minimal-level id check, a dropped watched path, the leftover-profile check) were each caught by the tests.
- First push: `scripts/catalog_check.py` and the full suite were not run (no checkout on the box). At the Tester fix they were run on nimo in a worktree: catalog_check PASS, full suite 734 tests OK (15 skipped). 140-142 don't collide with main's entries (highest 139).

## Findings worth knowing

- **Chiasmus writes `~/.chiasmus/chiasmus.db` on every start** unless `CHIASMUS_HOME` is set (and `~/.cache/chiasmus` with `cache=true` unless `CHIASMUS_CACHE_DIR` is). A plain `npm install` fails without `make` (tree-sitter-clojure builds from source); `--ignore-scripts` works for every other language. `dead-code` lists entry points too.
- **Tracekit's `demo --server` hard-codes `/tmp`** and fails under a read-only `/tmp`. A refused argument swap is a `gaps` WARN, not a FAIL, so gates must read `gaps`. Dev mode is same-user: real evidence needs a separate-user signer and a witness.
- **Charlotte in stdio mode loads `file://` URLs** (its SSRF guard is HTTP-mode only), so it can read whatever the account can: run it sandboxed with only the worktree visible. It does not exit on stdin EOF, and a SIGTERM without closing stdin first left its puppeteer profile in `TMPDIR` (3 of 3); EOF then SIGTERM cleaned up every time. `main` is 111 commits past the `v0.8.0` tag (107 past the commit npm published as 0.8.0).

## Tester FAIL fix (2026-10-21, on nimo)

Tester FAILed the first push (B01): the claim that every check had a test turning it false was untrue for 8 of 46 checks. Fixed by adding stub knobs and one test per check in `tests/test_x_intake_smoke_140_142.py`:

| Check | Test that now turns it false |
|------|------|
| chiasmus `driver_report` | `ChiasmusTests.test_crashing_server_fails_driver_report` (server exits on `chiasmus_graph`) |
| chiasmus `prolog_proves_reach` | `ChiasmusTests.test_prolog_never_true_fails` |
| chiasmus `reachability_true` | `ChiasmusTests.test_reach_never_fails` |
| tracekit `driver_report` | `TracekitTests.test_driver_error_fails_driver_report` (export raises) |
| tracekit `safe_calls_allowed` | `TracekitTests.test_safe_call_denied_fails` |
| tracekit `bundle_verifies` | `TracekitTests.test_good_bundle_rejected_fails` |
| tracekit `tamper_copies_made` | `TracekitTests.test_untamperable_layout_fails_tamper_copies` (spaced JSON, the flip edit finds nothing) |
| charlotte `full_has_body_text` | `CharlotteTests.test_full_without_body_text_fails` |

Also: a Chiasmus extra-tool test for `exact_9_tools` and a Tracekit rule-less denial test for `destructive_calls_denied`; a real-HOME change during an early exit 2 now has a test (FAILs with exit 1) and the joined reason no longer starts with `; ` when empty; the missing-Chrome exit 2 has an in-process test (the runner may have a system Chrome); `PFY_XINTAKE_TIMEOUT` that is not a finite number > 0 now exits 2 with a message instead of quietly using 600 s; an explicit `$CHIASMUS_NODE`, `$CHARLOTTE_NODE` or `$CHARLOTTE_CHROME` that is not an executable file exits 2 instead of falling back. Entry 140 package count corrected to 128 (`npm install --dry-run --prefix <scratch> --cache <scratch>` with the entry's flags on nimo; scratch removed), and the Charlotte distance re-read from the GitHub compare API (111 past `v0.8.0`, 107 past npm's `gitHead` `208f672`). No tool was installed on nimo; the smokes were not run against the real tools in this fix (stub tests only).

## Recommended next steps (not started)

1. **Eval-auto trial: Chiasmus for Reviewer.** Give Reviewer `chiasmus_graph` (impact, dead-code, cycles) and `chiasmus_verify` on three past pfy-mentat diffs with known review findings, Hermes plus `qwen3.6:35b` on nimo, stdio only, `CHIASMUS_HOME` in the worktree. Measure findings caught versus the existing Reviewer notes and the share of solver calls that parse. It would replace grep-based blast-radius reasoning in Reviewer briefs if it catches at least as much.
2. **Eval-auto trial: Tracekit receipts for one gate.** Route the Tester's Bash calls in one Build drop-in run through the Tracekit SDK with the `coding` pack, signer data under `tmp/`, then attach the verified `.tkb` to the gate receipt. Measure false denies, missed calls (compare with the harness log) and overhead. Pair with neatroots (137) rules over the same run.
3. Charlotte: a browsing task bake-off for local models (three small tasks on public docs pages) with Charlotte `core` against the current browser path, counting tokens per task and success. Needs network, so run it on nimo under bwrap with only the worktree visible.

## LATER (logged, not cataloged this run)

- **oly / open-relay** (@DanKornas, https://github.com/slaveOftime/open-relay; MIT, Rust): a local-first session supervisor that keeps coding-agent PTY sessions alive after the terminal closes, with human-in-the-loop check-ins. Overlaps tmux/systemd for long nimo Build runs; next run if a slot is free.
- **aios** (@DanKornas, rexleimo/aios): control plane with a ContextDB; overlaps Hermes and pfy routing. Low.
- herdr-reviewr, xmatrix, Operant, Foundry/promptise, ok-skills, awesome-agent-observability, Minke, Yao, the dsh-* DeepSeek Harness plugins, Satori, kotlin-footguns, ADK training: duplicates of the Hermes/Build/herdr niche, NOASSERTION licences, curated lists or off-core. Low.

TRADING (parked desks, no action): openInvest and dsh-fund-research.

SKIPPED: **Shpigford/chops** (the one @tom_doerr post: a skill organizer for coding agents, but a macOS-only Swift app; skill management is covered by Entry 075, and @tom_doerr posts are the weekly automation's territory), @alex_verem's video-editing list (auto-editor, LosslessCut, Buzz, FunClip, Video2X, HyperFrames already 070, rembg), aula-mcp, proxy-scraper, framefields, laya (aayushch), xiaoman, ritmo, an academic-commercialization repo, a McKinsey-style chart skill, and @yume_arasaki's DeepSeek V4.1 Flash recipe (DGX Spark only; no ROCm fit).

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through raw.githubusercontent and the public API). No accounts, sign-ins, paid keys or spend. Chiasmus, Tracekit and Charlotte ran only on the Grok Bot box in `/tmp` with temp HOMEs and no network; no model, agent CLI, installer, network listener or live site was used.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 140-142 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| A tool writes to the real HOME | `~/.chiasmus`, `~/.cache/chiasmus`, the Tracekit dirs or `~/.cache/puppeteer` change on nimo | The smokes fingerprint those paths (`home_sig`) before the run and in a finally, and FAIL on any change, also on timeout. Writes outside the watched paths (Chrome's own `~/.config/google-chrome` when `XDG_CONFIG_HOME` is unset) are not seen |
| Tracekit smoke over-read | PASS taken as "our runs are tamper-proof" | It covers the dev signer, same-user; the separate-user signer and witness are trial work |
| Charlotte with a system Chrome far from puppeteer's 148 | CDP calls break after a Chrome update | Use Chrome for Testing at puppeteer's pin under `tmp/`, linked as `tmp/charlotte/chrome/chrome` |
| `smoke_128_130` helpers change | Import breaks | The tests import the smoke end to end; move `home_sig` into `smoke.py` if it's reused again |
