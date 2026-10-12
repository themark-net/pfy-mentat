# Daily X intake handoff — 2026-10-10

Routine: daily X intake for pfy-mentat (Grok Bot). Sources this run: Mark's new X bookmarks and the watch list (@tom_doerr, @DanKornas and the rest of the routine's list) since the last run. Deduped against TOOLS.md, `data/tools*.json`, `sources/` (including the weekly Tom Dörr pull) and the routine's own log; none of the three tools below appeared anywhere in the catalog (the only Dicklesworthstone hit is `destructive_command_guard`, Entry 041, a different tool). Previous X intake slice (Entries 103-105) merged as PR #285; `main` had 105 as the highest entry when this slice was numbered.

## What this slice adds

| Entry | Tool | Why | Runs on nimo? |
|------|------|-----|---------------|
| 106 | [Rulora](https://github.com/Buffalo2024/Rulora) | Small Node controls: output validation by stage, bounded loops with an explicit `human_handoff`, frozen candidate selection. Pattern reference for loop exits and `./pfy decision` | Yes, npm `--prefix` under `tmp/`, no model. Smoke PASSed on the Grok Bot box |
| 107 | [HAR](https://github.com/os-factory/har) | Agent harness CLI + MCP: worktree slot per task, deterministic `verify --full` tied to the tree, teardown keeps the branch. Eval-auto candidate vs our Build `/orchestrator`-in-worktree lane | Yes, npm `--prefix` under `tmp/`, but only with `har telemetry off` and `HOME` under `tmp/` (default telemetry writes `~/.cursor/hooks.json` etc.; worktrees go to `$HOME/worktrees`). Smoke PASSed on the Grok Bot box |
| 108 | [cass-memory](https://github.com/Dicklesworthstone/cass_memory_system) | Procedural cross-agent memory: scored rule playbook, harmful marks deprecate, `cm context` at task start. MIT with an OpenAI/Anthropic rider | Yes, pinned release binary under `tmp/`, no keys; reflection only via local Ollama (not run). Smoke PASSed on the Grok Bot box |

Files: `sources/entries/106-rulora.md`, `107-har.md`, `108-cass-memory.md`, `examples/x-intake-local/smoke_106_108.py` (three new checks that reuse the helpers in `smoke.py`; `smoke.py`, `smoke_098_100.py` and `smoke_103_105.py` are unchanged), the folder README, and this handoff. No TOOLS.md rows, no `data/tools.json` rows, no stage cards, no Make target, no `.gitignore` change. Box receipts are not committed; commit receipts only from a real nimo run. Those receipt directories are gitignored, so committing a real nimo receipt uses `git add -f pipelines/smoke/<entry>/latest.json`.

This slice was written by the routine directly through the GitHub connector rather than `./pfy build -p`, since it is docs plus one stdlib script and nimo was not needed for it.

## How to gate

On nimo each `python3 examples/x-intake-local/smoke_106_108.py --entry rulora|har|cassmemory` should exit 2 with an operator reason, since nothing is staged under `~/DEVELOP/pfy-mentat/tmp` yet. To get a PASS, stage what the reason names:

- rulora: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/rulora --ignore-scripts @rulora/core@0.1.0-alpha.4` (Node 20+; or unpack an official Node tarball to `~/DEVELOP/pfy-mentat/tmp/rulora/node`).
- har: `npm install --prefix ~/DEVELOP/pfy-mentat/tmp/har --ignore-scripts @osfactory/har@1.16.0` (Node 20+). The smoke itself runs with a temp HOME and `har telemetry off`; do not run `har` by hand with the real HOME.
- cassmemory: `cass-memory-linux-x64` and `cass-memory-linux-x64.sha256` from the v0.5.0 release, checked, saved as `~/DEVELOP/pfy-mentat/tmp/cass-memory/cm` (`chmod +x`; sha256 `06e1563881f8bb1225cf7036068252ef210f242704a27f8ce32518b822181bd7`).

Or point `$RULORA_DIR`/`$RULORA_NODE`, `$HAR_BIN`/`$HAR_NODE`, `$CM_BIN` at a staged copy. Receipts go to `pipelines/smoke/<entry>/latest.json`. Each smoke FAILs (exit 1) on a bad output accepted or rejected at the wrong stage, a loop that does not hand off or accepts records after closing, a mutable frozen pool, an invented candidate accepted; a verify that does not pass on a green repo or does not fail on a broken test, a changed main checkout, a worktree left after teardown, agent hook files written with telemetry off; a matching rule missing from `cm context`, a deprecated rule still returned, or nonzero `cm usage` spend.

What was checked on the Grok Bot box (all in `/tmp`, temp HOMEs): the PASS path for all three, on Node 22.23.3 and (rulora) the box's Node 20.19.2, and again with networking removed (`unshare -rn`); the negative paths: no prereqs gives exit 2 for each, a stub `@rulora/core` whose loop never hands off gives exit 1, `PFY_XINTAKE_TIMEOUT=0.01` gives exit 1 with "telemetry off timeout" for har, and a wrong `$CM_SHA256` gives exit 2 without exec. `python3 -m py_compile` is clean.

Repo checks on the Grok Bot box, in a shallow clone of `main` at `fb3beb5` with this slice copied in: `python3 scripts/catalog_check.py` PASS (n_json=7). `python3 -m unittest discover -s tests -t .` ran 190 tests with 1 failure, `tests.test_hedge.DetectorTests.test_detector_runs_offline` (`'partial'` not in the allowed statuses), and `examples/eval-harness/run_structural.py` FAILs only on that same unittest line. Both are identical on untouched `main` on the box, so they come from the box environment, not this slice; the 2026-10-09 orch-decisions handoff recorded both green on nimo. `make` is not installed on the box.

## Recommended next steps (not started)

1. **Eval-auto trial: HAR vs the headless Grok Build `/orchestrator`-in-worktree lane + Tester/Reviewer sha pinning** on one small pfy-mentat task. `HOME` under `~/DEVELOP/pfy-mentat/tmp/har-home`, `har telemetry off` first, `har env init --profile cli --no-agents --no-cursor-rule --commit-gate never` in a throwaway clone (never Mark's main checkout), `verificationStages` set to our real checks (`python3 -m unittest discover -s tests -t .`, `make eval-structural`, `python3 scripts/catalog_check.py`). Run the same task once through our lane and once through a HAR slot; compare setup time, whether the recorded pass matches the head sha Tester/Reviewer pin, and what HAR's evidence adds. It would replace our hand-rolled worktree setup and "checks ran at this sha" step, not the Tester/Reviewer judgment. Run when nimo isn't in a benchmark.
2. Rulora: no trial. If useful, copy the `LOOP_CLOSED` / `UNKNOWN_CANDIDATE` contracts into pfy tests for the loop skills and `./pfy decision`.
3. cass-memory: only after Mark reads the license rider. Then a Grok/local-only trial against the handoff-doc + AGENTS.md routine (and the opencode-mem toolset candidate): stage `cass` under `tmp/`, index a week of Build logs, `provider: ollama` with the decision-bench pick, and check whether `cm context` surfaces rules a fresh agent would miss.

## LATER (logged, not cataloged this run)

- **preflight** — https://github.com/newrelic-experimental/preflight. Local-first coding-assistant observability; Claude/Codex-focused. Next run if slots.
- **agentenv-framework** — https://github.com/scaleapi/agentenv-framework. RL/eval environments SDK; heavier.
- **metis** — https://github.com/Wholiver/metis. Evidence-backed coding agent; overlaps the harness lane (now Entry 107).
- **concord-mcp** — https://github.com/Get-Concord-AI/concord-mcp. Multi-agent same-repo coordination MCP; overlaps Foremerge (097).
- **akm** — https://github.com/itlackey/akm. Skills/memory library CLI; overlaps skill packs.
- **octocode** — https://github.com/Muvon/octocode. Rust code-intel MCP; overlaps Ix (084).

## Locks respected

Catalog 70-75 HOLD untouched. Nothing installed or downloaded on nimo. Mark's main checkout and stashes untouched; a read-only shallow clone of public `main` in `/tmp` on the Grok Bot box was used only for dedupe greps. No accounts, sign-ins, paid keys or spend. Tools were tested only on the Grok Bot box in `/tmp` with temp HOMEs; no model was called by any of them.

## How this fails / how we recover

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Entry numbers collide | Another branch also adds 106-108 | Renumber on rebase; entries are self-contained files |
| Smoke in CI without prereqs | Exit 2 read as red | Not wired into CI or Make; exit 2 is the honest "can't run here" |
| HAR touches real agent config | Someone runs `har env launch` with the real HOME and default telemetry | Entry and smoke say telemetry off + temp HOME; smoke FAILs on hook files |
| Rulora alpha churn | Class, code or status renamed | Smoke FAILs with "API shape changed?"; pin `@rulora/core@0.1.0-alpha.4` |
| cass-memory license | Use drifts into an OpenAI/Anthropic-model lane | Grok/local lanes only until Mark decides; noted in the entry |
| cass-memory release churn | JSON shape or deprecation threshold changes | Binary sha pinned; smoke FAILs with a reason |
