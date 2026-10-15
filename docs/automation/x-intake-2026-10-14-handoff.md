# X intake 2026-10-14: handoff (Entries 117-118)

Daily X intake routine, window 2026-10-14 00:39Z to 2026-10-15 00:36Z (Mark's bookmarks plus the watch list). Two catalog entries at **I0** plus one stdlib smoke script and a folder README paragraph. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. Previous slices #292 (112-114) and #293 (115-116) are both merged; `main` was `2c9f7b4` with 116 as the highest entry when this branch was cut.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 117 | [Kander](https://github.com/dualface/kander) (MIT, Go, v0.9.5) | Terminal kanban that runs coding agents in parallel git worktrees, with read-only PMQA and Security reviewer agents before a card is done. Supports Grok and OpenCode. **Eval-auto candidate** vs today's single headless `/orchestrator` run followed by bot gates | Yes, one binary under `tmp/kander`, `HOME` under `tmp/`. Smoke PASSed on the Grok Bot box |
| 118 | [MCP Moira](https://github.com/moira-mcp/moira) (Apache-2.0, v6.0.0) | Self-hosted workflow engine: node graph, per-step completion conditions and input schemas, driven over MCP. Comparison point for how we encode loop exits | Only with Docker (unconfirmed on nimo; installing it needs Mark). Not run anywhere yet |

Files: `sources/entries/117-kander.md`, `118-moira.md`, `examples/x-intake-local/smoke_117_118.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py`; every child goes through `run_isolated`), a paragraph in `examples/x-intake-local/README.md`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target, no `.gitignore` change. Box receipts are not committed.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_117_118.py --entry kander|moira` should exit 2 with an operator reason until staged:

- kander: download `kander-linux-amd64.tar.gz` from the v0.9.5 release (not `latest`), check it against the release's `checksums.txt`, and unpack it into `~/DEVELOP/pfy-mentat/tmp/kander/`. Needs git and tmux.
- moira: only if Docker is already on nimo. Put upstream's `docker-compose.yml` and `config/traefik-self-host.yml` (from the v6.0.0 tag) in `~/DEVELOP/pfy-mentat/tmp/moira/`, copy `.env.example` to `.env` there, generate its secrets locally, and set `MOIRA_IMAGE` to the v6.0.0 image pinned by digest. If Docker isn't installed, leave this entry catalog-only; installing it is a nimo system change that needs Mark.

Receipts go to `pipelines/smoke/<entry>/latest.json`.

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs): kander PASS under bwrap (read-only root, no network). Negative paths: no binary gives exit 2; `$KANDER_VERSION=9.9.9` gives 2; a wrong `$KANDER_SHA256` gives 2; `PFY_XINTAKE_TIMEOUT=0.001` gives exit 1 with "kander version timeout". The box's real `~/.agents` and `~/.config/kander` did not appear. moira: no staged dir gives 2; no docker gives 2; an image tagged `:latest` gives 2; with a stub `docker` whose `up` fails, the smoke exits 1 and still runs `compose down`. The happy path of the moira smoke has **not** run anywhere. `python3 -m py_compile` is clean. The repo's `scripts/catalog_check.py` and unit tests were not run in this slice (no checkout on the box); Tester should run them on the PR head.

## Findings worth knowing

- **Kander supports Grok as executor and reviewer**, and limits Grok and OpenCode reviewers to read tools. Cursor, Pi and Devin reviewers rely on the prompt only, per upstream.
- **Kander defaults to codex** (falling back to opencode) for the executor and both reviewers when it writes its config, so a trial must pick Grok explicitly.
- **Kander writes outside the repo on first run** (`~/.agents/kander`, `~/.config/kander`) and rewrites its rule files on every `doctor`. Run it with `HOME` under `tmp/` on nimo.
- **Moira defaults to `:latest`**, and its `.env` holds an auth secret and an admin password. Pin by digest; keep `.env` under gitignored `tmp/`.

## Recommended next steps (not started)

1. **Eval-auto trial: Kander vs the headless `/orchestrator` run.** Pick three small pfy-mentat backlog items. Run them once through the current lane (one Build run, then Tester and Reviewer bots) and once through Kander with Grok as executor and a read-only reviewer (Grok, or OpenCode on a local model on nimo), each in a throwaway worktree under `tmp/` with `HOME` under `tmp/`. Compare: cards that reached done without Mark, must-fix issues the in-loop reviewer caught before the bot gates, Bot turns spent, Build usage, wall time, and any merge conflicts between parallel cards.
2. Moira: only after Docker is confirmed on nimo. Model the X intake loop's exits as one Moira workflow and see whether the completion conditions catch a step that our current prompt lets slide.

## LATER (logged, not cataloged this run)

- **Sno Station** — https://github.com/sno-ai/sno-station (Apache-2.0). Shared encrypted memory and handoffs across agent CLIs, including when one hits its usage cap. Installs with `curl | sh` into `~/.local/bin`, and its default Agent Native mode uploads each day's sessions to Sno's cloud unless turned off. Revisit in Local First mode only.
- **Sovereign-OS** — https://github.com/Justin0504/Sovereign-OS (MIT). Charter-driven org (CEO plans, CFO approves budget, ledger tracks spend) that mirrors our agent org. Needs an Anthropic or OpenAI key for its planner; agent backends can be any headless CLI. Revisit if the planner can point at a local model.
- **Maestro** — https://github.com/josstei/maestro-orchestrate (Apache-2.0). Multi-agent orchestration for Gemini CLI, Claude Code, Codex and Qwen Code; overlaps Kander and the orchestrator lane.
- **Ullage** — https://github.com/dualface/ullage-cli (Kander's author). Local CLI that reads subscription usage for Grok, Cursor and others; might feed the usage log in #274. It would read our auth files, so check what it touches before any trial.
- **Best of Agent Harnesses** — https://github.com/RyanAlberts/best-of-Agent-Harnesses (CC-BY-SA-4.0). Weekly-rescored ranked list of 167 harnesses; a possible extra intake source, not a tool.
- **Traceway** — https://github.com/tracewayapp/traceway (MIT). Self-hosted OpenTelemetry logs, traces and AI tracing. Posted by @tom_doerr, so left for Mark's weekly tom_doerr automation.
- Matt Pocock on a `GRILL.md` to customize his `/grill-me` planning skill without editing it: a pattern for our skills (a small per-repo override file), no artifact.

SKIPPED: BugPatrol (already Entry 103) and colibri (already Entry 003), both re-posted; ZizkaDB and Joxo (license NOASSERTION); Faucet (SQL to REST/MCP, off our pipeline); invisible_dots (computer-use VMs built to evade anti-bot checks); Agent Skills CLI (marketplace installer); codex-claude-code-config (overlaps Entry 076); dsh-agent-team (DeepSeek Harness only); IvyClaw, AI WorkDeck, Sentient OS (macOS), ChatterMate, Docmost, ShellRS, the Roblox tools, homelable, the agent-frontend platform, Awesome Free LLM APIs (needs provider signups), AI Bootcamp and Awesome AI Pulse lists; @yume_arasaki's DGX Spark and RED-SNOW (321B, EXL3) runs (NVIDIA only, too big for nimo); @ch3nweiii's two-frontier-model team (needs paid frontier APIs); @_avichawla's SFT/DPO/RLVR explainer; replies and newsletter posts. No new bookmarks since the last run.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector and raw URLs). No accounts, sign-ins, paid keys or spend. Kander ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model or agent was started.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 117-118 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| Kander trial writes to the real HOME | Rules land in `~/.agents` on nimo | Set `HOME` under `tmp/`; the smoke FAILs if the real HOME changes |
| Moira smoke happy path untested | Fails the first time Docker is there | Treat the first nimo run as the real test; fix the smoke in a follow-up |
