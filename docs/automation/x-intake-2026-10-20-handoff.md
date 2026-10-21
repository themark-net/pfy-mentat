# X intake 2026-10-20: handoff (Entries 137-139)

Daily X intake routine, window 2026-10-20T00:36Z to 2026-10-21T00:39Z. Sources: Mark's latest 40 bookmarks (13 not seen before) and 142 watch-list posts (6 pages; none from @tom_doerr in the window). Three catalog entries at **I0**, one stdlib smoke script with a unit-test file, a folder README paragraph and `.gitignore` lines for receipts. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. #304 (131-133) merged at `a393a91`; main has since gained 134-136 (Hermes Agent, Monid, Harness²), so this branch is cut from `main` at `24fe672` and numbering continues at 137.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 137 | [neatroots](https://github.com/neatlogs/neatroots) (Apache-2.0, TypeScript, v0.2.9) | Local-first trace checks for agent runs; `neatroots check` gates saved traces offline with an exit code, project rules as YAML; local decision model is Laya (086). **Possible eval-auto trial** | Yes: a 17 MB bundle plus Node 22+ under `tmp/`. Smoke PASS on the Grok Bot box |
| 138 | [Hermes Teammates](https://github.com/100yenadmin/hermes-teammates) (MIT, Python, 1.1.0 at `de85f5d4793e`) | Named subagent roster for Hermes Agent (stock core): fixed reviewer/tester briefs, narrowed toolsets, a SQLite run ledger, steering, Kanban review lane. Mark chose Hermes as the bot interface on 2026-10-20. **Eval-auto trial after the Hermes wiring** | Yes, inside the isolated Hermes from 134. Config and ledger smoke PASS on the box |
| 139 | [OpenCode Skill Creator](https://github.com/antongulin/opencode-skill-creator) (Apache-2.0, TypeScript, 0.3.6) | Validate skills and measure whether their descriptions trigger, through `opencode run` on a local model | Yes: npm prefix under `tmp/`. Smoke PASS on the box (validate/parse and start-up side effects) |

Files: `sources/entries/137-neatroots.md`, `138-hermes-teammates.md`, `139-opencode-skill-creator.md`, `examples/x-intake-local/smoke_137_139.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py` and `home_sig`, `finish`, `as_json`, `pkg_version`, `tmo` from `smoke_128_130.py`; every child goes through `run_isolated`; the real-HOME paths are fingerprinted with `home_sig` before the run and in a finally), `tests/test_x_intake_smoke_137_139.py` (55 stub-based tests), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{neatroots,teammates,skillcreator}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

Written by the routine through the GitHub connector rather than `./pfy build -p`: docs plus one stdlib script, nimo not needed. Pushed as a branch with no PR (Mark's 2026-10-19 rule): gate this branch at its pinned head, then fast-forward `main`.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_137_139.py --entry neatroots|teammates|skillcreator` should exit 2 with an operator reason until staged:

- neatroots: `mkdir -p ~/DEVELOP/pfy-mentat/tmp/neatroots/app && cd ~/DEVELOP/pfy-mentat/tmp/neatroots && curl -LO https://github.com/neatlogs/neatroots/releases/download/v0.2.9/neatroots.tar.gz && echo "4c6c66ba65646080a0b6726dbbd2e1b9a5502e564beb501eb948a82e7c3de35a  neatroots.tar.gz" | sha256sum -c && tar xzf neatroots.tar.gz -C app`. If nimo's `node` is older than 22, unpack `node-v24.14.1-linux-x64.tar.xz` from nodejs.org into `tmp/neatroots/node` (strip the top dir). Never run `install.sh`, `neatroots connect`, `init` or `start`.
- teammates: `git clone https://github.com/100yenadmin/hermes-teammates ~/DEVELOP/pfy-mentat/tmp/hermes-teammates && git -C ~/DEVELOP/pfy-mentat/tmp/hermes-teammates checkout de85f5d4793e122cde98342bddd6e1bf3cd53459`. Never `hermes plugins install` against `~/.hermes`.
- skillcreator: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/opencode-skill-creator --ignore-scripts --no-audit --no-fund opencode-skill-creator@0.3.6` (tarball sha256 `eef1b5e9f9b9a77d744c39eade57a11a8233062ab50e812824c094fb8f627deb`). Never run its `install` command.

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored; `$PFY_SMOKE_RECEIPT_DIR` overrides).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap 0.12.0 with no network):

- **neatroots PASS** (0.2.9, Node 24.14.1): clean run 0; three identical `lookup_order` calls fire `repeated-tool-call` (count 3); a fake `sk-` key in model output fires `secret-in-output` and is never echoed; a `--checks` `requires_before` rule fires only on the refund-without-lookup run (13 library rules + 1); `--only` narrows; an unparsable file exits 2; the `TMPDIR` scratch dir is removed.
- **teammates PASS** (1.1.0 at `de85f5d4793e`, no Hermes): roster parse fails closed on an unknown key, a bad name and empty toolsets; absent toolsets inherit; long instructions clipped to 4,000 and still valid; `max_live_runs: 99` falls back to 4; ledger cap 2 refuses a third live run per session; `finish()` is a single terminal CAS.
- **skillcreator PASS** (0.3.6, Node 20.19.2): 14 tools via a fake V2 ctx; `skill_validate` accepts a good skill, rejects an unknown key, a non-kebab name and a missing `SKILL.md`; bundled skill only under the temp `XDG_CONFIG_HOME`; no update check with auto-update off.
- Negative paths: wrong pins (`NEATROOTS_VERSION=0.2.8`, `HT_COMMIT=abc`, `OSC_VERSION=0.3.5`), a missing app/clone/package and Node 20 for neatroots each give 2.
- Unit tests: 55/55 OK in about 10 s (fake `node` for neatroots and the skill creator, fake git clone for teammates). Each check has a test that turns it false, plus temp-HOME writes, real-HOME writes without bwrap for every watched path, a write into the clone, and timeouts that keep the real-HOME check. Four hand mutants of the smoke (Node floor, secret echo, admission cap, update-check file) were each caught by the tests.
- **Not run here** (no checkout on the box): `scripts/catalog_check.py` and the full suite. 137-139 don't collide with main's entries (highest 136). Please run both on the head.

## Findings worth knowing

- **neatroots `check` needs a writable `TMPDIR`** (EROFS and exit 2 otherwise, the same code as bad input). `--checks` is variadic, so trace files go first. `requires_before` selects tool spans with `tool:`; selectors are strict. `install.sh` writes `~/.neatroots`, `~/.local/bin`, shell profiles and agent MCP configs.
- **Hermes tool search defers plugin tools** (Hermes Teammates README): with `tools.tool_search.enabled: auto` the teammate tools sit behind `tool_search`/`tool_call`. That is the same setting as Entry 134's open follow-up, so settle it once for both.
- **OpenCode Skill Creator writes on every start**: the bundled skill goes to the user-level OpenCode skills dir, and unless `OPENCODE_SKILL_CREATOR_AUTO_UPDATE=0` it checks npm daily and can remove OpenCode's cached copy of itself. Its validator allows only six frontmatter keys.

## Recommended next steps (not started)

1. **Eval-auto trial: neatroots `check` as the bake-off failure gate.** Convert one Hermes bake-off run and one JevAgentHarness run (Entry 131 `steps.jsonl`) to Neatlogs HTTP JSONL or OTLP, write our rules (repeated call, unrecovered tool failure, narrated-not-called tool) as YAML under `.neatroots/checks/`, and compare its findings with the hand-written oracle in `examples/hermes-bakeoff/`. It would replace the custom repeated/failed-call counting if it agrees on every run; Laya-backed questions can follow.
2. **Eval-auto trial: Hermes Teammates for the Tester/Reviewer loop**, once the Hermes wiring from 134 lands. Isolated `HERMES_HOME`, Ollama `qwen3.6:35b`, a roster of `tester` and `reviewer` with narrowed toolsets, three small gate tasks, tool search on and off. Measure assignment success, valid tool-call rate and ledger accuracy. It would replace hand-written delegation briefs to Build/Hermes subagents.
3. OpenCode Skill Creator: run `skill_validate` read-only over pfy-mentat's skills, then `skill_eval` on two or three skills with OpenCode on a local engine and `XDG_CONFIG_HOME` in the worktree. No current tool to replace; it adds a missing trigger check.

## LATER (logged, not cataloged this run)

- **Vibe-Skills** (@DanKornas, Apache-2.0, 3.7k stars): skill router and workflow orchestrator, claims +21.12 pp SkillsBench reward and -29.6% tokens. Big (31 MB) and installs into agent homes; compare with 122/123 routers and 139 later.
- **Hermes Official Plugins** (Nous Research, MIT) and **Footprint** (Hermes plugin, @witcheer via an @DanKornas repost): look at them with the Hermes wiring.
- **MenteDB**, **Cortex Hub**, **Trail-code**, **Pensieve** (macOS app): memory and context layers; overlap 108 and 132.
- **Agent Usage** (Herdr plugin), **Agentbox** (GPL-3.0 GUI), **touri** (macOS), **cloudroom-core**, **engrams** (AGPL, Firecracker), **ShibaClaw**, **Conch**, **Nexus Cloud**: agent runners and dashboards, mostly duplicate what Hermes/Build give us.
- **REA Reconstruction Companion**, **schemagate**, **dif**, **bunflared**, **IsleDB**, **OpenContracts**, **MulmoChat**, **gtrk CLI**, **doc-haus**: off-core or narrow.
- **Phonon** (@alex_verem; Gradium on-device voice model): check license and weights for the career-capture voice interviewer; not pfy-mentat catalog.
- **AI Job Search** (@alex_verem; already logged 2026-10-19 from a bookmark): Gom Jobbar and job-search track, not a catalog tool.
- NVIDIA **GLM-5.3-Flash FP4-Local** and **Qwen3.8-Flash-Next FP4-Local** (@yume_arasaki): NVFP4 for DGX Spark/RTX PRO; no fit on ROCm. **TandemLLM** (@DanKornas): DGX Spark only.

TRADING (parked desks, no action): bookmarks for Polymarket copy-trading (@leshuuuk) and a memecoin trade audit (@WhiteWhaleLabs); @ch3nweiii's "QUANT DESK" Claude Code post.

SKIPPED: money and marketing bookmarks (cold email, startup lists, Okara CMO, OpenShip Mail pricing, Monid launch post, already Entry 135), the Grok Bot cost posts, Pixel TUI library, the Supabase rebuild post, image models (Krea 3, Fibo 2.0, MOSS), reading lists (awesome agent papers, research radars, AI resources), Grandet (API price shopping), papers and opinion posts, and replies.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through raw.githubusercontent and the public API). No accounts, sign-ins, paid keys or spend. neatroots, Hermes Teammates and OpenCode Skill Creator ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model, agent CLI, server or installer was started.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 137-139 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| A tool writes to the real HOME | `~/.neatroots`, `~/.hermes/plugin-data/hermes-teammates` or the skill creator's OpenCode paths change on nimo | The smokes fingerprint those paths (`home_sig`) before the run and in a finally, and FAIL on any change, also on timeout. Writes outside the watched paths are not seen |
| Teammates smoke over-read | PASS taken as "works in Hermes" | It covers config and ledger only; the Hermes run is next step 2 |
| `smoke_128_130` helpers change | Import breaks | The tests import the smoke end to end; move `home_sig` into `smoke.py` if it's reused again |
