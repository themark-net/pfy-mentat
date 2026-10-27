# X intake 2026-10-26: handoff (Entries 146-147)

Daily X intake routine, window 2026-10-23T00:50Z to 2026-10-27T00:40Z (the 10-23 to 10-25 runs did not complete, so this run covers four days). Sources: Mark's 40 latest bookmarks (9 new) and 589 watch-list posts (24 pages). Two catalog entries at **I0**, one stdlib smoke script with a unit-test file, a folder README paragraph and `.gitignore` lines for receipts. Catalog-only; not a Feature GO, and nothing here competes with the pfy-mentat MVP. Catalog HOLD 70-75 untouched. 143-145 are on `main` (`7b716e8`, the gate-fix head); this branch is cut from `main` at `7b716e8` (highest entry 145), so numbering continues at 146.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 146 | [skill-up](https://github.com/alibaba/skill-up) (Apache-2.0, Go, v0.14.0) | Declarative evals for Agent Skills and agents with a custom local-command engine, graded results and exit 1 on any failed case: a scoring harness for H1/H2 and for the pfy-mentat vs Grok Build trial. **Eval-auto trial candidate** | Yes: static release binary under `tmp/skill-up`. Smoke PASS on the box and on nimo |
| 147 | [HiRoute](https://github.com/higress-group/HiRoute) (Apache-2.0, v0.3.1) | Local per-message difficulty router and gateway for agent clients: hard turns to the primary model, routine turns to a cheap or local one, with per-session receipts. Compare with HarnessRouter (123) | Yes for the daemon: x86_64 binaries, no GPU. Smoke PASS on the box and on nimo (temp-HOME install only). Routing to a model not tried |

Files: `sources/entries/146-skill-up.md`, `147-hiroute.md`, `examples/x-intake-local/smoke_146_147.py` (imports `TMP`, `_bwrap_prefix`, `find_bin`, `pinned`, `write` from `smoke.py`, `as_json`, `finish`, `home_sig` from `smoke_128_130.py`, `SYS_PATH`, `bad_override`, `iso`, `system_python`, `timeout_problem` from `smoke_140_142.py` and `sha256_file` from `smoke_143_145.py`; every child goes through `run_isolated`; the real-HOME paths are fingerprinted before the run and in a finally), `tests/test_x_intake_smoke_146_147.py` (35 stub-based tests), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{skill-up,hiroute}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Receipts are not committed.

Written by the routine on the Grok Bot box and pushed through the GitHub connector rather than `./pfy build -p`: docs plus one stdlib script. Pushed as a branch with no PR (Mark's 2026-10-19 rule): gate this branch at its pinned head, then fast-forward `main`.

## How to gate

Both tools are already staged on nimo (downloads only, digests checked, nothing installed):

- `~/DEVELOP/pfy-mentat/tmp/skill-up/skill-up` from `skill-up_0.14.0_linux_amd64.tar.gz` (sha256 `307f2082ce5489c61f6a01ce6c78225dfd3974b4b54227426b87e1b6330dbfc9`; binary `5b1bdd0a30f57653c8f6a3a679e992b29982fe18709b2556d53a6f9ea1c85ab6`).
- `~/DEVELOP/pfy-mentat/tmp/hiroute/` holding `hiroute-0.3.1-13856abd873d-x86_64-unknown-linux-gnu.tar.gz` (`dfa35ada...d21aa`), its `.tar.gz.json` manifest (`e7e313ac...74509`) from the [v0.3.1 release](https://github.com/higress-group/HiRoute/releases/tag/v0.3.1), and `standalone.py` from `https://hiroute.ai/install/standalone.py` (`3a7ef92f...9b7c2`). Never run `install.sh` or the installer with the real HOME.

Then, in a worktree of this branch under `~/DEVELOP/pfy-mentat/tmp`:

```sh
python3 examples/x-intake-local/smoke_146_147.py --entry skill-up   # expect PASS
python3 examples/x-intake-local/smoke_146_147.py --entry hiroute    # expect PASS (needs bwrap)
python3 -m unittest tests.test_x_intake_smoke_146_147               # 35 tests
python3 scripts/catalog_check.py
```

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored; `$PFY_SMOKE_RECEIPT_DIR` overrides).

What was checked (box: `/tmp`, temp HOMEs, bubblewrap with no network; nimo: the same script files copied to `~/DEVELOP/pfy-mentat/tmp/xi-146-147`, receipts there, Python 3.14.4, kernel 7.0.0-38, bwrap 0.11.1):

- **skill-up PASS on the box and on nimo**: `--version` 0.14.0; `validate` loads 2 cases; `run --output-dir` exits 1 with "1 passed, 1 failed, 0 errors"; result.json has ping-pass PASS (`pong-7`) and hello-fail FAIL with must_contain evidence; the stub agent got one SessionInput per case; temp HOME empty; fixture unchanged; `~/.skill-up` and `~/.config/skill-up` untouched.
- **hiroute PASS on the box and on nimo**: offline install into the temp HOME (all marker paths inside it); local control ready; `system status` role_all, gateway ready; gateway on `127.0.0.1:<auto>`; unpublished `/v1/models` 503 `GATEWAY_PUBLICATION_UNAVAILABLE`, ungranted chat 401 `GATEWAY_GRANT_UNAUTHORIZED`; `routing.preview` and `decision.services.test` in `schema list`; SIGTERM exit; the eight real-HOME installer paths untouched.
- Unit tests: 35 OK on the box and on nimo. Each recorded check has a test that turns it false, plus the exit-2 guards (missing binary, bad override, sha and version pins, bad timeout, not staged, no bwrap). The skill-up real-HOME test runs without bwrap; the hiroute real-HOME watch is tested in-process on `watched` for each of its eight paths (bwrap's read-only root stops a stub from writing the parent HOME).
- `scripts/catalog_check.py` was run on the box on this branch (see the commit status in the run report). The full repo unittest suite was not run for this branch.

## Findings worth knowing

- **HiRoute's installer reaches into agent config.** It writes `~/.local/bin/hiroute{,d}`, `~/.local/lib/hiroute`, `~/.local/share/hiroute`, a systemd user unit, and a `hiroute-management` skill into both `~/.agents/skills` and `~/.claude/skills`, then runs `systemctl --user daemon-reload`. The daemon refuses to start without the installer's marker, so there is no "just unpack and run" path. Any trial needs a dedicated trial HOME under `tmp/hiroute`.
- HiRoute's documented decision model is a hosted Alibaba Bailian endpoint; whether a local decision model works is unverified and is the first question for a trial. It bundles CLIProxyAPI for subscription proxying (not configured here).
- **skill-up's `validate` takes the eval.yaml path; `run` takes the skill dir** and exits 1 when any case fails. Without `--output-dir` it writes `<skill>-workspace/` next to the skill.
- **Berth** (T-Crypt/berth v0.3.6, a GPU lease broker aimed at the kind of GPU contention that locked nimo up on 2026-10-06) was the third keeper candidate but was **dropped after a check on nimo**: its daemon reports `[ERROR] gpu inventory: GPU observation unavailable: AMD: card1 is not an available RDNA3/RDNA4 discrete or Phoenix APU amdgpu card` for nimo's Strix Halo (PCI `1002:1586`), and `berth run --fail-closed` then refuses (exit 75, "berthd unreachable"). The binary (sha256 `eef40302...49b13`) was run from `~/DEVELOP/pfy-mentat/tmp/berth` with a temp HOME; nothing installed. Revisit if a release adds Strix Halo.

## Recommended next steps (not started; after the MVP work)

1. **Eval-auto trial: skill-up as the scorer for "pfy-mentat vs plain Grok Build".** Replaces the ad hoc pass/fail judgement planned for DevBot's small-batch trial (MVP item: Grok, then a local model, against plain Grok Build) with a fixed case set and graded receipts. Write 10-20 cases from recent Build tasks (rule and script checks only, no Agent Judge), wrap each harness as an `engine.custom` local command, run all three, compare pass rate, time and turns. Also reusable for H1 (score a harness2 candidate before adopting it) and H2 (score a discovered skill with vs without). No keys, no spend; runs under `tmp/skill-up` on nimo.
2. HiRoute: once the MVP lands, a trial HOME under `tmp/hiroute` with nimo's local model as the economical tier and a local decision model if it supports one; compare routing quality and cost against HarnessRouter (Entry 123). Needs Mark's OK before any subscription or hosted judge.

## LATER (logged, not cataloged this run; cap 3)

OmniRoute and respan-gateway (gateways; overlap HiRoute), LambdaTest/rook (agent-task verification; check whether it needs their cloud), MentisDB, rtk-ai/icm, krusch-context-mcp, loci, walrus-memory (memory lane), arcee-ai/nac (long-running harness), jrswab/axe (single-purpose agents CLI), nkapila6/mcpsurfr (keyless local web search MCP), strands-agents/box (sandbox; overlaps the bwrap path), agent-trace, TraceVista, traceAI (trace viewers; overlap Entry 141).

SKIPPED: hyperresearch (@tom_doerr; left to Mark's weekly automation), OpenUI (skipped 2026-10-15), REA (already cataloged), gpu-unlock forks (NVIDIA only), @alex_verem's security-tools list, Claude/Codex/DeepSeek-Harness-specific plugins and UIs, macOS-only or paid cloud tools, model news and benchmarks, and the 9 new bookmarks (two trading posts, launch and backlink lists, accelerator deadlines, Lavender stats, Parano1d, Bend bank, survival-llm). No trading tools this run.

## Locks respected

Catalog 70-75 HOLD untouched. On nimo, only downloads into `~/DEVELOP/pfy-mentat/tmp/{skill-up,hiroute,berth,xi-146-147}`; nothing installed, no system packages, no systemd unit. Mark's main checkout and stashes untouched (it was only looked at with `git status`). HiRoute's installer ran only with throwaway temp HOMEs inside bubblewrap with no network. No accounts, sign-ins, paid keys or spend; X read only. No model, agent CLI or live site was used.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 146-147 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| A tool writes to the real HOME | skill-up config or HiRoute install paths change on nimo | The smokes fingerprint those paths before the run and in a finally and FAIL on any change. Writes elsewhere in HOME are not seen |
| HiRoute installer changes upstream | `standalone.py` is not versioned | Its sha256 is pinned; a new file exits 2 until re-reviewed |
| Shared helpers move | Import from `smoke_140_142`/`smoke_143_145` breaks | The tests import the smoke end to end; move shared helpers into `smoke.py` if reused again |
