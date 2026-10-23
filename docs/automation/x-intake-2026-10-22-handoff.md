# X intake 2026-10-22: handoff (Entries 143-145)

Daily X intake routine, window 2026-10-22T00:37Z to 2026-10-23T00:36Z. Sources: Mark's 40 latest bookmarks (read again this run; the X connection is back) and 107 watch-list posts (5 pages), 114 of them new. Three catalog entries at **I0**, one stdlib smoke script with a unit-test file, a folder README paragraph and `.gitignore` lines for receipts. Catalog-only; not a Feature GO, and nothing here competes with the pfy-mentat MVP. Catalog HOLD 70-75 untouched. 140-142 are on `main`; this branch is cut from `main` at `346bf44` (highest entry 142), so numbering continues at 143.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 143 | [taste-skill](https://github.com/Leonxlnx/taste-skill) (MIT, zero-dependency Node, commit `6010f91`) | Agent design skills with a seeded direction draw, a static slop linter and a headless-Chrome page check that exit 1 on slop: a machine-checkable design floor for the Design-in-loop rule. **Possible eval-auto trial as a Design gate** | Yes: 2.5 MB clone under `tmp/`, Node 22+ and a Chrome. Smoke PASS on the Grok Bot box |
| 144 | [gitai](https://github.com/feder-cr/git-ai) (MIT, Go Gitaly fork, v0.3.1) | Open Scion-style Git server: many agents land short changes on one branch by compare-and-swap, with per-agent tokens and branch policy. Matches pfy-mentat's parallel Build workers | Probably, but a heavy source build (Go 1.26, make, meson, ninja). Catalog-only: smoke exits 2 on the box (can't build) |
| 145 | [Muxin](https://github.com/LumaryLabsLLC/muxin) (Apache-2.0, Rust, 0.6.0) | One app and MCP server (89 tools, read-only and destructive annotated) for a fleet of machines and their agent sessions: a fleet view over nimo, borg, maximum, plant and beelink. **Eval-auto candidate for Sysadmin** | Yes: release binary under `tmp/`, no GPU or keys. Smoke PASS on the box in demo mode |

Files: `sources/entries/143-taste-skill.md`, `144-gitai.md`, `145-muxin.md`, `examples/x-intake-local/smoke_143_145.py` (imports `TMP`, `find_bin`, `pinned`, `write` from `smoke.py`, `as_json`, `finish`, `home_sig` from `smoke_128_130.py`, and `iso`, `bad_override`, `timeout_problem`, `node_major`, `tree_hash`, `system_python`, `MCP_CLIENT`, `CHROMES`, `SYS_PATH` from `smoke_140_142.py`; every child goes through `run_isolated`; the real-HOME paths are fingerprinted before the run and in a finally), `tests/test_x_intake_smoke_143_145.py` (58 stub-based tests), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{taste-skill,gitai,muxin}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

Written by the routine through the GitHub connector rather than `./pfy build -p`: docs plus one stdlib script, nimo not needed. Pushed as a branch with no PR (Mark's 2026-10-19 rule): gate this branch at its pinned head, then fast-forward `main`.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_143_145.py --entry taste-skill|gitai|muxin` should exit 2 with an operator reason until staged:

- taste-skill: `git clone https://github.com/Leonxlnx/taste-skill ~/DEVELOP/pfy-mentat/tmp/taste-skill && git -C ~/DEVELOP/pfy-mentat/tmp/taste-skill checkout 6010f91a9935f1c167dfc500fb1a475681892e6b`. If nimo's `node` is older than 22, unpack `node-v24.14.1-linux-x64.tar.xz` from nodejs.org into `tmp/taste-skill/node` (strip the top dir). An installed `chromium`/`google-chrome` is picked up, or set `$TASTE_CHROME`. Never `npx skills add` or copy it into an agent's skill dir.
- gitai: `git clone --branch v0.3.1 https://github.com/feder-cr/git-ai ~/DEVELOP/pfy-mentat/tmp/gitai`, then `make build` there by hand, only if Go 1.26, make, meson and ninja are already available under `~/DEVELOP` (no system packages without Mark). Until then the smoke exits 2, which is the expected result for this gate.
- muxin: download `Muxin-0.6.0-linux-x86_64.tar.gz` and `SHA256SUMS.txt` from the [v0.6.0 release](https://github.com/LumaryLabsLLC/muxin/releases/tag/v0.6.0), check sha256 `0d12438c5dff60c1688e666fa688579e0ca8fc1a6fdc13fb7f0a25f6ffdce837`, and unpack into `~/DEVELOP/pfy-mentat/tmp/muxin` (giving `tmp/muxin/Muxin/muxin`). Never run its `install.sh`. If `muxin --version` fails on missing `libxkbcommon-x11.so.0` or `libxcb-xkb.so.1`, `apt-get download` those two .debs, `dpkg -x` them under `tmp/muxin/libs` and set `$MUXIN_LIB_DIR` to the `usr/lib/x86_64-linux-gnu` dir inside (no install).

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored; `$PFY_SMOKE_RECEIPT_DIR` overrides).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap with no network):

- **taste-skill PASS** (commit `6010f91`, Node 24.14.1, system Google Chrome): lint on the slop fixture exits 1 with `emoji, eyebrow, gradient, lorem, purple`, on the clean fixture exits 0 with no findings, on a missing path exits 2; the seeded `--options 3` menu is identical twice and writes nothing; a full draw writes `direction.json` into `--out` and history only to the temp `TASTE_SKILL_HISTORY`; `inspect.mjs` fails the slop page (`gradient`, `emoji`, `eyebrow`, `focal-point`, `edge-text`, `off-centre`) with two JPEG screenshots and no profile left; temp HOME empty.
- **muxin PASS** (0.6.0, binary sha pinned, the two X libraries from .debs via `LD_LIBRARY_PATH`): paths under `MUXIN_HOME`; 9 demo machines; MCP over stdio with 89 tools, 17 destructive (`run_on_machines`, `cloud_destroy`, `vm_destroy`, `process_signal`, ...), `status` read-only and summarising 9 machines; `get_machine forge` found, an unknown id `not_found` naming the known ids, a wrong argument `invalid`, a demo `run_on_machines` `succeeded`; exit on stdin EOF; temp HOME and `XDG_STATE_HOME` empty.
- **gitai exit 2**: not built ("missing _build/bin/gitaly, gitaly-hooks, gitaly-ssh, graft, graft-cache"). Its quickstart path is covered by stub tests only.
- Negative paths: a wrong `MUXIN_VERSION` gives 2; wrong commit pins and sha pins give 2 in the tests.
- Unit tests: 58/58 OK in about 14 s (a fake `node` for the three taste-skill scripts, a fake `muxin` binary with an MCP server, and a real git repo with a bash quickstart for gitai). Each recorded check has a test that turns it false, plus temp-HOME writes, real-HOME writes without bwrap for the watched paths, a `make` shim refusing other targets, a server that ignores EOF, and timeouts that keep the real-HOME check. Four hand mutants against the real tools (slop fixture swapped for clean, an extra expected inspect id, 8 expected demo machines, a demo run on an unknown id) each FAILed.
- **Not run here** (no checkout on the box): `scripts/catalog_check.py` and the full suite. 143-145 don't collide with main's entries (highest 142). Please run both on the head.

## Findings worth knowing

- **taste-skill's full draw writes `~/.taste-skill/history.json`** unless `TASTE_SKILL_HISTORY` is set, and `--out` defaults to `.taste-skill/` in the cwd. `inspect.mjs` is opinionated: our "clean" bakery fixture still FAILs `palette-cream` and `measure`, so its FAILs are Design's call until Design Bot picks an `--allow` list. Chrome leaves `~/.local/share/{applications,pki}` when `XDG_DATA_HOME` is unset.
- **Muxin's MCP server wrote `$HOME/.local/state/gh/device-id` in demo mode** in an earlier probe without `XDG_STATE_HOME`; the smoke sets it to a temp dir and watches the real path. `--demo` goes after the subcommand. A source build of 0.6.0 needs a newer rustc than 1.85.1. 17 of 89 tools are destructive across every configured host.
- **gitai's quickstart always runs `make build` first**, and its own pass signal is just a printed line, so the smoke checks the bare repo's branches itself and swaps `make` for a no-op shim.

## Recommended next steps (not started; after the MVP work)

1. **Eval-auto trial: Muxin as Sysadmin's read-only fleet view.** Configure Muxin under `tmp/muxin` with `MUXIN_HOME` there and a dedicated read-only SSH user on nimo, borg and plant, expose only the 40 read-only MCP tools to Sysadmin through Hermes, and compare a week of "what's running where, what needs attention" answers against Sysadmin's current ad hoc ssh checks (accuracy, turns, time). It would replace those ssh status checks if it is at least as accurate. Needs Mark's OK for the SSH user.
2. **Eval-auto trial: taste-skill lint as a Design gate floor.** Run `lint.mjs` (hard FAIL) and `inspect.mjs` (advisory) on the next operator-UI branch for pfy-mentat or Leasegrid, and have Design Bot rule on each FAIL. Measure how many FAILs Design agrees with. It would add to the screenshot-by-eye review, not replace it.
3. gitai: a scratch-repo trial of three parallel Build workers landing on one branch, once a local Go 1.26 toolchain under `~/DEVELOP` is available.

## LATER (logged, not cataloged this run)

- **diagram-design** (@tom_doerr, cathrynlavery/diagram-design; MIT): a diagram skill; @tom_doerr posts are the weekly automation's territory, and it overlaps 143.
- **OpenAdapt** (MIT): demonstration-to-program desktop automation. Low.
- **Automatos AI** (@DanKornas): a self-hostable agent OS; overlaps Hermes. Low.
- @_avichawla's Google resumable-agent post: the underlying tool wasn't resolved.

TRADING (parked desks, no action): a MrMilkTrading indicators bookmark.

SKIPPED: duplicates HarnessRouter (Entry 123), cloudflare/security-audit-skill (Entry 127) and mattpocock/skills (already covered); notion-mcp-server (needs a Notion token); nyacg/pagedb (Cloudflare Durable Objects, off-core); Underdog Bark 3.0 (not an open repo); Moss-Image-Edit (off-core); Tenki (an X article only); @yume_arasaki's DeepSeek V4.1 Flash DGX benchmarks (NVIDIA only); @alex_verem's prompts and news and the Meta tokenizer paper; bookmarks on startup deadlines, Grok Bot use cases and Minimax LoRAs.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through raw.githubusercontent). No accounts, sign-ins, paid keys or spend; X was read only. taste-skill and Muxin ran only on the Grok Bot box in `/tmp` with temp HOMEs and no network; no model, agent CLI, installer, real host or live site was used. gitai was cloned and read on the box; its build was attempted and failed for missing tools.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 143-145 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| A tool writes to the real HOME | `~/.taste-skill`, `~/.config/graft`, `~/.cache/graft`, `~/.config/muxin` or `~/.local/state/gh` change on nimo | The smokes fingerprint those paths before the run and in a finally and FAIL on any change, also on timeout. Writes elsewhere in HOME are not seen |
| Muxin trial reaches a real host | A destructive tool runs on nimo | Demo mode only in the smoke; the trial uses a read-only tool allowlist and a read-only SSH user |
| gitai smoke untested on real binaries | The first real run fails on a detail the stubs miss | First nimo run is a hand run; fix the smoke then |
| `smoke_140_142` helpers change | Import breaks | The tests import the smoke end to end; move the shared helpers into `smoke.py` if they're reused again |
