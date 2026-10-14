# X intake 2026-10-12: handoff (Entries 112-114)

Daily X intake routine, window 2026-10-12 00:34Z to 2026-10-13 00:40Z (Mark's bookmarks plus the watch list). Three catalog entries at **I0** plus one stdlib smoke script. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. Previous slice: #287 (Entries 109-111), merged; `main` had 111 as the highest entry.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 112 | [Overtime](https://github.com/ukanwat/overtime) (MIT, npm 0.5.3) | Persistent agents as folders that outlive sessions: daemon wakes, daily budgets, protected paths, numbered questions, drives any ACP agent. **Eval-auto candidate** as the wake/budget/resume layer around unattended Grok Build runs vs today's one-shot headless `/orchestrator` run | CLI and daemon yes, under `tmp/overtime` with Node >= 22.19 and `HOME` under `tmp/`. A real run needs a usable ACP backend (Grok Build if it speaks ACP, unverified; or OpenCode + local Ollama). Smoke PASSed on the Grok Bot box |
| 113 | [Festival](https://github.com/Obedience-Corp/festival) (Apache-2.0, v0.3.20) | Plan, gates and `fest next` live in files and git so any harness (Grok Build named upstream) resumes. Comparison point for orchestrator + loop-exits + Tester/Reviewer gates + handoffs | Yes, static binaries under `tmp/festival`, `HOME` under `tmp/`. Smoke PASSed on the box under a read-only root with no network |
| 114 | [Sloptrim](https://github.com/seyedehsanhadi/sloptrim) (Apache-2.0, v0.9.4) | Stdlib, offline 0-100 score for AI-writing patterns in prose files; a cheap Reviewer/Design check on bot-written docs, pairs with Entry 105 | Yes, a clone under `tmp/sloptrim`, system python3. Smoke PASSed on the box under a read-only root with no network |

Files: `sources/entries/112-overtime.md`, `113-festival.md`, `114-sloptrim.md`, `examples/x-intake-local/smoke_112_114.py` (reuses `write` and `TMP` from `smoke.py`; the other smoke scripts are unchanged), the folder README, `tests/test_x_intake_smoke_112_114.py`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. `.gitignore` ignores `pipelines/smoke/overtime/`, `pipelines/smoke/festival/`, and `pipelines/smoke/sloptrim/` (`pipelines/smoke/kolibri1/latest.json` stays tracked). Box receipts are not committed.

Fix after Tester FAIL on PR 292: `node --version` and sloptrim `git rev-parse` get that same reduced env (a temp HOME, only `PATH` / `HOME` / `TERM` / `LANG` / `NO_COLOR`). `sh()` starts a new session and SIGKILLs the process group on timeout. bwrap adds `--unshare-pid` when the probe accepts it, and still runs without that flag when the probe does not. Overtime `daemon stop` runs in a `finally`, and the real `~/overtime` check still runs when a command times out. `tests/test_x_intake_smoke_112_114.py` plants fake key sentinels and a stub grandchild under a 1s `PFY_XINTAKE_TIMEOUT`; both fail on the code from the first PR head.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_112_114.py --entry overtime|festival|sloptrim` should exit 2 with an operator reason until staged under `~/DEVELOP/pfy-mentat/tmp`:

- overtime: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/overtime --ignore-scripts @ukanwat/overtime@0.5.3`, plus Node >= 22.19 at `tmp/overtime/node/` (nodejs.org `latest-v22.x` linux-x64 tarball, checked against `SHASUMS256.txt`) if nimo's Node is older.
- festival: `festival-0.3.20-linux-x86_64.tar.gz` from the v0.3.20 release (sha256 `0202a7b15cc385d1687d756ae6f513283a5adef445037f70a054b754e6ec716f`, in its `checksums.txt`), unpacked as `~/DEVELOP/pfy-mentat/tmp/festival/` (the smoke pins `fest` and `camp`).
- sloptrim: `git clone --depth 1 --branch v0.9.4 https://github.com/seyedehsanhadi/sloptrim.git ~/DEVELOP/pfy-mentat/tmp/sloptrim`.

Or point `$OVERTIME_DIR`/`$OVERTIME_NODE`, `$FEST_BIN`, `$SLOPTRIM_DIR` at a staged copy. Receipts go to `pipelines/smoke/<entry>/latest.json`.

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs): all three PASS. Negative paths: no prereqs gives exit 2 for each; Node 20 gives exit 2 for overtime; `$OVERTIME_VERSION=9.9.9` gives 2; a wrong `$FEST_SHA256` gives 2 without exec; a wrong `$SLOPTRIM_COMMIT` gives 2; `PFY_XINTAKE_TIMEOUT=0.001` gives exit 1 with a timeout reason. After the runs no Overtime daemon was left and the box's real `~/overtime`, `~/.obey` and `~/campaigns` did not exist. `python3 -m py_compile` is clean.

Repo checks on this worktree after the Tester fix: before the fix, `tests.test_x_intake_smoke_112_114` was 2 tests and 3 failures. After the fix, `python3 -m unittest discover -s tests -t .` ran 206 tests, OK (skipped=4). `python3 scripts/catalog_check.py` PASS (`n_json=7`, toolsets=6 linked=2 catalog_tool=null:4, tools_md=51 stage_cards=51 i1_cards_open=0 stage_only=4).

## Findings worth knowing

- **Overtime budget guard**: the README says a change to AGENT.md's settings block by anything other than the app is put back "so no agent can raise its own budget". On the box a plain file edit raising `dailyBudgetUsd` to 999, made while no session was running, was logged as "adopted the settings you edited in AGENT.md" and applied. The smoke records this as `agent_md_edit_adopted` without failing. An agent's own edit during a session was not tested. Any trial must check this before trusting the budget.
- **Overtime defaults**: new agents use the `claude` backend with a $100/day budget. Never `send` before setting backend, budget and tokens.
- **Festival** refuses to hand out work from an unfilled plan (`fest next` exits 1 with "VALIDATION FAILED"), and strict `--agent` create rolls back. That is the fail-closed behavior we want from a loop.

## Recommended next steps (not started)

1. **Eval-auto trial: Overtime around unattended Grok Build** vs today's one-shot headless `/orchestrator` run. First check whether nimo's `grok` CLI has an ACP mode; if it does, add it under `customBackends` in a temp-HOME `~/overtime/settings.json`; if not, use OpenCode + local Ollama as the backend instead. One agent, workspace a throwaway worktree under `tmp/`, `protect=` Mark's main checkout, a small daily budget and token cap, one real backlog item. Compare hours of useful progress without a human, number of questions raised, budget adherence (including the AGENT.md finding), and how cleanly it resumes after a session ends.
2. Festival: one side-by-side on a pfy-mentat backlog item in a throwaway camp, compared with the orchestrator lane's plan and handoff.
3. Sloptrim: score 20 existing handoff docs and PR bodies to see whether the numbers match what reviewers would flag before wiring it anywhere.

## LATER (logged, not cataloged this run)

- **Pydantic Deep Agents** — https://github.com/vstorm-co/pydantic-deepagents (MIT). Self-hosted terminal agent and Python framework; overlaps harnesses we have.
- **DSH Crew** — https://github.com/ZSeven-W/dsh-crew (MIT). Dispatch DeepSeek Harness agents from Claude Code/Codex/Grok; DSH-specific.
- **Munder Difflin** — https://github.com/HarnessMD/munder-difflin (MIT). Desktop office of terminal coding agents; GUI.
- **HERMES** (paper via @alex_verem): one model per file in a codebase; technique, no artifact linked.
- **GLOSSARY.md** from Matt Pocock's `/grill-with-docs`: a small, usage-grown glossary so agents speak the repo's language; technique note for AGENTS.md.

SKIPPED: jev-mcp (needs a TypeSafe Jev key; Entry 086 Laya is the local Jev-compatible path), SubQ Snap (hosted model), Skales (license NOASSERTION), Anthropic-Cybersecurity-Skills (off-scope), clearcam, NASA Worldview, myPKA, AgenticOS, OpenInstinct, MindRoom, CharDesk, Software Periodic Table, browser games, news and jokes. Bookmark @gurgavin stop-loss thread: trading, parked desks only, no action.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector). No accounts, sign-ins, paid keys or spend. Tools ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model was called. No installer scripts were run.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 112-114 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| Overtime daemon left running | Smoke killed mid-run | `finally` runs `daemon stop`; the daemon lives in a temp HOME that is removed |
| Parent env reaches a child | `node --version` or sloptrim `git rev-parse` inherited the parent environment | Those children get the same reduced env as the tool commands (temp HOME, five variables) |
| Timeout leaves a grandchild | Only the direct child was killed | `sh()` uses a new session and SIGKILLs the process group; bwrap adds `--unshare-pid` when the probe accepts it |
| Timeout skips the real-HOME check | `TimeoutExpired` unwound before the `~/overtime` compare | The compare runs after the timeout is caught; a change fails the smoke |
| Release churn | Festival and Overtime both shipped on 2026-10-12 | Binaries sha-pinned, versions and commits pinned; smokes exit 2 with a reason |
