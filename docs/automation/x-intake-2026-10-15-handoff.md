# X intake 2026-10-15: handoff (Entries 119-121)

Daily X intake routine, window 2026-10-15 00:36Z to 2026-10-16 00:38Z (Mark's bookmarks plus the watch list). Three catalog entries at **I0** plus one stdlib smoke script, a folder README paragraph and three `.gitignore` lines for receipts. Catalog-only; not a Feature GO. Catalog HOLD 70-75 untouched. The previous slice #295 (117-118) is merged; `main` was `fe6f01a` with 118 as the highest entry when this branch was cut.

| Entry | Tool | Why | Fits nimo? |
|------|------|-----|------------|
| 119 | [AgentDescent](https://github.com/Birfy/agentdescent) (MIT, Python, 0.5.1) | Parallel, merge-based self-evolution of skill folders, prompts and harnesses against a cases file, with a ledger and an explicit `apply`. **Eval-auto candidate** vs today's hand or Build edits to skills and the planned DSPy step in the toolsets drop-in | Yes, venv under `tmp/`, local model via an OpenAI-compatible endpoint. Smoke PASSed on the Grok Bot box |
| 120 | [Kenfold](https://github.com/jeonjw85/kenfold) (MIT, Go, v0.1.1) | Self-hosted shared memory for several agent CLIs over MCP, with per-agent provenance and secret rejection | Only with Docker (unconfirmed on nimo; installing it needs Mark). Not run anywhere yet |
| 121 | [Tree-sitter Analyzer](https://github.com/aimasteracc/tree-sitter-analyzer) (MIT, Python, 2.2.0) | Local code-intelligence MCP/CLI (structure, call graph, change impact, mis-wire audit). Third option next to codebase-memory-mcp and Graphify | Yes, venv under `tmp/`, no model. Smoke PASSed on the Grok Bot box |

Files: `sources/entries/119-agentdescent.md`, `120-kenfold.md`, `121-tree-sitter-analyzer.md`, `examples/x-intake-local/smoke_119_121.py` (imports `TMP`, `find_bin`, `pinned`, `run_isolated`, `timeout_reason` and `write` from `smoke.py`; every child goes through `run_isolated`), a paragraph in `examples/x-intake-local/README.md`, `.gitignore` lines for `pipelines/smoke/{agentdescent,kenfold,tsa}/`, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target. Box receipts are not committed.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_119_121.py --entry agentdescent|kenfold|tsa` should exit 2 with an operator reason until staged:

- agentdescent: `python3 -m venv ~/DEVELOP/pfy-mentat/tmp/agentdescent/.venv` then `.venv/bin/pip install agentdescent==0.5.1`.
- tsa: a venv at `~/DEVELOP/pfy-mentat/tmp/tree-sitter-analyzer/.venv` (Python 3.10+) with `pip install "tree-sitter-analyzer[all]==2.2.0"`. Don't use the README's `curl | bash` installer.
- kenfold: only if Docker with Compose is already on nimo. `git clone --branch v0.1.1 https://github.com/jeonjw85/kenfold ~/DEVELOP/pfy-mentat/tmp/kenfold`. If Docker isn't installed, leave this entry catalog-only; installing it is a nimo system change that needs Mark.

Receipts go to `pipelines/smoke/<entry>/latest.json` (gitignored).

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs, bubblewrap with no network): agentdescent PASS (demo reward 1.000, learned `COLUMN: amount`, skill on disk untouched, temp HOME empty); tsa PASS (structure listed `tax` and `total`; `miswire-audit` indexed python:3 and javascript:1 and reported 0 TSA mis-wires). Negative paths: no binary gives exit 2 for both; `$AGENTDESCENT_VERSION=9.9` and `$TSA_VERSION=1.0.0` give 2; `PFY_XINTAKE_TIMEOUT=0.001` gives exit 1 with "tsa version timeout". kenfold: no staged dir gives 2; a staged dir with no docker gives 2. The kenfold happy path has **not** run anywhere (no Docker on the box). `python3 -m py_compile` is clean. The repo's `scripts/catalog_check.py` and unit tests were not run in this slice (no checkout on the box); Tester should run them on the PR head.

## Findings worth knowing

- **AgentDescent's default run store is `~/.agentdescent/runs`**, outside DEVELOP on nimo. Pass `--store` (or `$AGENTDESCENT_HOME`) under `tmp/`. Its demo agent is a local program, so the demo proves the loop, not model quality.
- **Kenfold prints API keys once to stdout** (`make key`). Put them straight into a secret store; never paste or log them. Its own image is built from source, so the pin is the git tag; Postgres is pinned by tag, not digest. Set `KENFOLD_UPDATE_CHECK=false` to stop it calling GitHub.
- **TSA's `miswire-audit` writes `.ast-cache/` into the audited repo.** Use a throwaway worktree. On our tiny fixture a name-only resolver also scored 0, so the claimed advantage still needs a real repo.

## Recommended next steps (not started)

1. **Eval-auto trial: AgentDescent vs how we tune skills today.** Pick one pfy-mentat skill with a clear pass/fail (for example the X intake triage rules or `org-spinny-decide`). Write 20-30 cases with known answers, keep a held-out third, and run `agentdescent evolve` with `openai_compatible` pointed at the local endpoint on nimo (`qwen3.6:35b`), store under `tmp/`. Compare against the current skill and against one DSPy pass from the toolsets drop-in: held-out score, local-model wall time, and how readable the `show` diff is. Only `apply` through a normal PR with Tester and Reviewer.
2. TSA: run `miswire-audit` and `--safe-to-edit` on a pfy-mentat worktree and add a TSA column to `docs/evaluation/codebase-memory-vs-graphify.md`.
3. Kenfold: only after Docker is confirmed on nimo. Stdio mode against the compose Postgres, embeddings pointed at nimo's Ollama, one agent (OpenCode) writing and reading handoff memories.

## LATER (logged, not cataloged this run)

- **super-board** (@DanKornas). Claude Code skill pack that moves GitHub Project cards through Build, QA and Review on its own. Claude Code only; overlaps Entry 117 (Kander) and the orchestrator lane.
- **critty** (@DanKornas). Terminal UI for reviewing AI-written plans and diffs and sending inline feedback back to the agent. Possible human-in-the-loop helper for Mark; no artifact checked yet.
- **ReMe** (@DanKornas). Local-first agent memory kept as Markdown files. Overlaps Entry 120 and the memory notes; check the repo and license next time it shows up.
- **Funzzy (fzz)** (@DanKornas). Rust file watcher that runs YAML-defined checks on change for agents. Generic dev tool; revisit if the edit loop needs one.
- **OpenGateLLM** (@DanKornas). Self-hosted LLM API gateway. Overlaps the existing LiteLLM/Ollama example.
- **Paperclip** (@DanKornas). Open-source agent orchestration dashboard (goals, tasks, costs). Cross-reference for Entry 050 (paperclipai/companies).
- **Human Edge Agent Skills** (@DanKornas). 18 portable `SKILL.md` workflows (ambiguous decisions, voice input, writing, deploy). Could be skimmed for decision-skill ideas.
- **rutis** (@DanKornas). Hot-reloadable plugin runtime for agents across Rust, TypeScript, Python and Go.
- Matt Pocock on getting agents to build state machines or reducers for robustness and testability: a pattern note for Build drop-ins, no artifact.
- Trading desks only (parked, no action): **Oracle3** (@DanKornas), an MCP server and Python tools for Kalshi and Polymarket fee and price checks.

SKIPPED: Llamatik (Kotlin on-device apps), Infisical (secrets platform, off our pipeline), Auto Runtime (source-available, not open), BrowserCode (browser sandbox for hosted coding CLIs), tuxevil-rotator (rotates provider accounts), Skill of Skills (directory), Brow and GhosttyEXTREME (macOS only), ClaudeWatch and pixtuoid (Claude Code session dashboards), CamouFlow (anti-detect browser profiles and proxies), Physical AI OS (robot hardware), fauxnix (Windows), the Roblox MCP bridge, dcc-mcp-core (creative-app control), squirrelscan (website SEO QA), ManimCat, Manor AI, pi-subagents (pi only), Zero to AI course, WordCraft/GridCraft office clones, OpenUI 1.0 (generative UI, off scope), Kling 4, Krea 3, Flux 3 Klein, Fish Audio Drama 3 TTS, the TaoMate LoRA, Topview 3D Builder (image/video/audio models), @ch3nweiii's Claude Code folder post, @_avichawla's GPU interview question, and opinion, news and health posts. @tom_doerr's face-recognition post was left to Mark's weekly tom_doerr automation. No new bookmarks since the last run.

## Tester FAIL @ 6d6962b fixed (B1)

- `smoke_119_121.py` now snapshots the real-HOME dirs each tool can write before the run and compares them in a `finally`, so `checks["real_home_untouched"]` is set on timeout too (the #295 kander pattern): agentdescent `~/.agentdescent` (default run store), tsa `~/.tsa` (sessions) and `~/.cache/tree-sitter-analyzer`, kenfold `~/.local/state/kenfold` (hook state) and `~/.cache/kenfold` (bench cache).
- Partial checks are kept in the receipt on timeout, and a `compose down -v` timeout no longer overwrites an earlier failure reason (recorded as `down_reason`).
- Kenfold is pinned to commit `dfc18f9f` as well as tag `v0.1.1` (a moved or local tag no longer passes).
- New `tests/test_x_intake_smoke_119_121.py`: planted real-HOME writes FAIL, timeout keeps checks, down timeout keeps the reason, wrong pins / no docker / busy port exit 2, receipts gitignored.
- Still open: postgres and the build base images are tag-pinned, not digest-pinned; the Kenfold happy path has still not run with real Docker.

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; no pfy-mentat checkout was made (files read through the GitHub connector and raw URLs). No accounts, sign-ins, paid keys or spend. AgentDescent and TSA ran only on the Grok Bot box in `/tmp` with temp HOMEs; no model or agent CLI was started.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 119-121 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| AgentDescent writes to the real HOME | `~/.agentdescent` appears on nimo | `--store` under `tmp/`; the smoke snapshots the real `~/.agentdescent` and FAILs (`real_home_untouched`) if it changed, also on timeout, and FAILs if its temp HOME is written |
| Kenfold smoke happy path untested | Fails the first time Docker is there | Treat the first nimo run as the real test; fix the smoke in a follow-up |
