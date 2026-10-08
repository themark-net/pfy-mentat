# Build drop-in: finish atg-framework autonomously (one paste, no questions)

Paste everything below the line into a fresh Grok Build window on nimo. It is safe to paste again: it resumes from its own run log. This replaces running `atg-framework.md` and the ATG parts of `pfy-mentat.md` by hand.

---
You are the **lead orchestrator** for finishing atg-framework: Zhang et al. (2026), arXiv:2607.01942, typed action graphs with localized repair. Mark (the founder) pre-authorized everything below and is asleep or away. **Never ask a question.** Run until every phase is done or exits blocked.

## Autonomy contract
- If something is ambiguous, pick the most conservative reversible option. Write one line about it in `docs/ops/AUTONOMOUS-DECISIONS-<date>.md` (choice, alternatives, why) and keep going.
- If a phase is blocked (missing dependency, host busy past its wait budget, repeated failure), mark it BLOCKED in the run log with the exact reason and next step, then move to the next phase it doesn't depend on. Never wait on a human.
- Use sub-agents if your harness supports them (task, agent or spawn tools). Give each workstream below to its own sub-agent, running independent ones in parallel and joining at the gates. Each sub-agent gets this contract, its phase text, and the paths, and reports back files changed, tests run, and numbers. If there are no sub-agents, run the phases yourself in order.
- Keep your context small. After each phase, write results to the run log and drop the details from memory.
- The founder's rules: tests check behavior and fail-and-recover, never tautological units. Every work item ends with a handoff doc in `docs/`. Never merge, because Tester and Reviewer gate merges. Never post on X. Nothing goes outside `~/DEVELOP/<project>`, `/tmp`, or the project's `tmp/`. No sudo, system packages, or service changes. No paid API keys: local models only.

## Resume protocol (do this first, every time)
1. `cd ~/DEVELOP/atg-framework && git fetch --all`. Read AGENTS.md, docs/NEXT.md, docs/USING.md, docs/DECISIONS.md, docs/OPEN_QUESTIONS.md and docs/ops/pfy-mentat-handoff.md.
2. Historical: that session already created its worktree on branch `build/atg-finish`. Do not create another one from this brief. **Never touch the main checkout**, which holds uncommitted founder edits.
3. Historical: if that session's `docs/ops/RUN-LOG-atg-finish.md` is still present, it records the first phase not marked DONE or BLOCKED. Otherwise the phase checklist below is the record of what that run did.
4. Also read pfy-mentat's local-model results so you don't redo them: `~/DEVELOP/pfy-mentat/docs/dogfood/LOCAL-BENCH-4-EDGE.md`, plus `LOCAL-BENCH-5-RUNTIMES.md` if it exists (`git -C ~/DEVELOP/pfy-mentat fetch && git -C ~/DEVELOP/pfy-mentat show origin/main:docs/dogfood/LOCAL-BENCH-5-RUNTIMES.md`).

## Host-quiet gate (used by phases C, D and E)
nimo is a 128 GB Strix Halo (Linux sees about 107 GB; GPU GTT is 96 GiB). Load a model only when **all** of these hold: `ollama ps` is empty, no other `llama-server`, `vllm` or `lemonade` model is loaded, there's no other bench (`pgrep -af 'bench.py|run_nommap'` is empty), and MemAvailable is at least model size + 25 GiB. If the host isn't quiet, poll every 5 minutes for up to 3 hours, logging each check, then mark the phase BLOCKED (host busy). Load one model at a time, and unload it when done (Ollama `keep_alive:0`, or kill your own llama-server). Never stop or pause processes you didn't start.

## Phases
**A. OpenAI-compatible client (no model needed; sub-agent 1).** `OpenAICompatClient` in `src/atg/llm.py`, stdlib only. Env: `ATG_BASE_URL`, `ATG_API_KEY` (optional), `ATG_MODEL`. Same `complete`/`complete_structured` contract as `OllamaClient`. Use `response_format` json_schema, falling back to a JSON instruction plus Pydantic validation. Add `--client {ollama,openai}` to `examples/toy_parallel.py`.
DoD: an E2E test against a tiny local `/v1/chat/completions` server. The first reply is malformed and the second is valid, so `run_task` recovers and the sink is 25. In a second test the server times out and you get `LLMError`, not a hang. Write the Decision record.

**B. Paper PoC suite (no model needed; sub-agent 2, parallel with A).** `examples/poc_suite.py`: 10–12 synthetic tool-DAG tasks, 4 of them with injected tool failures. Three arms: ATG localized repair, global replan (repair region = whole graph), and a sequential runner. Metrics per arm: success, LLM calls, tool calls, frozen-node reuse, repairs and wall time. Write JSON + markdown under `docs/poc/`, offline with `MockLLM` and live with any client.
DoD: an offline test asserts from the report that localized repair uses fewer LLM calls than global replan at equal success. Write the Decision on metric definitions and credit the paper in docs/ATTRIBUTION.md.

**Gate AB.** `uv run pytest -q -m "not integration"` is green (record the count). Commit A+B.

**C. Live toy remeasure (host-quiet; depends on A).** First the Decision 0017 check exactly as in NEXT.md step 1: `uv run python examples/toy_parallel.py --live --model qwen2.5:14b --only`. Supersede 0017 and set the default only on exit 0 with `max_parallel >= 2` and sink `{'value': 25}`; otherwise record stderr on 0017's revisit note. A killed process (143) isn't a model result: retry once.

**D. Model and runtime sweep (host-quiet; depends on A and B).** This is a separate comparison and doesn't change the default (the founder authorized it, so the NEXT.md "don't load 35b for this check" rule applies only to phase C). Run `poc_suite.py` live:
- `qwen3.6:35b` on Ollama
- `qwen3-coder-next` on llama-server with mmap off via `--client openai`: `/usr/local/lib/ollama/llama-server --no-mmap -ngl 999 -c 8192 -np 1 -fa on`, with env `GGML_BACKEND_PATH=/usr/local/lib/ollama/rocm_v7_2/libggml-hip.so`, `HSA_OVERRIDE_GFX_VERSION=11.5.1`, `GGML_CUDA_ENABLE_UNIFIED_MEMORY=1`, `GGML_HIP_UMA=1`, and the model blob from `ollama show --modelfile qwen3-coder-next`. See pfy-mentat `pipelines/dogfood/local-bench-4/run_nommap_server.sh`.
- Lemonade (server on port 13305, llama.cpp backend, OpenAI API) with qwen3.6:35b, if LOCAL-BENCH-5 shows it working.
- vLLM only if `import vllm` works in an existing venv. Don't install system packages to make it work.
Record per arm × model: success, LLM calls, repairs, valid-plan rate, and wall time. Also record the parallel ready-queue width actually reached. If LOCAL-BENCH-5 already measured a runtime's speed, cite it instead of re-benching.

**E. Paper-claims writeup (depends on B, plus D if it ran).** `docs/poc/RESULTS.md`: which of the paper's claims this repo now reproduces in miniature (fewer calls with localized repair, parallel waves, typed validation catching bad plans before execution), which it doesn't, and why (Decision 0018 defers the paper environments). Paper numbers stay attributed. Mark it clearly as a toy-scale reproduction.

**F. pfy-mentat integration (separate repo and PR; depends on C or D giving at least one live pass).** The founder authorizes this session to edit pfy-mentat for this phase only, which overrides NEXT.md step 3's "later session" for tonight. Follow `~/DEVELOP/pfy-mentat/docs/build-dropins/pfy-mentat.md` exactly, in its own worktree `~/DEVELOP/pfy-mentat/tmp/build-local-lane` on `build/local-lane-atg`: the llama-server lane, the atg-compile bench and the ATG catalog card refresh. Promote the stage only to I2, and only on a live pass. Never self-promote further. If C and D both failed, skip F and log why.

**G. Handoffs and PRs (always run, even after blocks).**
- atg-framework: write `docs/ops/HANDOFF-atg-finish-<date>.md` (what landed, commands, measured numbers, blocked items with next steps), update docs/NEXT.md and TODO.md, and make the final RUN-LOG commit. Push `build/atg-finish`. PR body goes to `/tmp/pr-atg-finish.md`. Open the PR with `gh pr create --body-file` if gh is authed; otherwise print `https://github.com/themark-net/atg-framework/compare/main...build/atg-finish?expand=1` and put the body path in the handoff.
- pfy-mentat (if F ran): the same, with `/tmp/pr-pfy-local-lane.md`, a dated section prepended to docs/PENDING-HANDOFF.md, and a `sources/entries/<next>-atg-*.md` entry.
- Final message: a phase table (DONE, BLOCKED or SKIPPED with reason), key numbers, PR URLs or compare URLs, and the autonomous-decision count.

## Hard stops (end the run, write G first)
- Tests on main were red before you started and you can't make them green in 2 attempts.
- nimo shows a lockup sign: swap at 100% with MemAvailable under 5 GiB. Unload everything you loaded, log the conditions (model, size, free memory, other processes), and skip the remaining live phases.
- About 6 hours of wall time have passed. Write G and stop. Re-pasting this prompt resumes the run.
