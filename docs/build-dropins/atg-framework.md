# Build drop-in: atg-framework, paper PoC slice

Paste everything below the line into Grok Build on nimo.

---
Repo: `~/DEVELOP/atg-framework` (GitHub themark-net/atg-framework). Read AGENTS.md, docs/NEXT.md, docs/USING.md, docs/DECISIONS.md (0011–0020) first.
Work in a worktree: `git fetch && git worktree add /tmp/atg-poc -b build/atg-poc origin/main`. Do not touch the main checkout, which may hold uncommitted founder edits.

Goal: turn the mock-only loop into a runnable proof of concept for Zhang et al. (2026), arXiv:2607.01942, on local models only.

Build:
1. `OpenAICompatClient` in `src/atg/llm.py`, stdlib only. Env: `ATG_BASE_URL` (e.g. `http://127.0.0.1:8080/v1`), `ATG_API_KEY` (optional), `ATG_MODEL`. Same `complete` / `complete_structured` contract as `OllamaClient`. Send `response_format` as `json_schema`. If the server rejects it, fall back to a plain JSON instruction plus Pydantic validation. Select it in `examples/toy_parallel.py` with `--client openai`.
2. `examples/poc_suite.py`: 8–12 synthetic tool DAG tasks (arithmetic, string, lookup tools), some with an injected tool failure. Three arms: ATG localized repair, global replan (region forced to the whole graph), and a sequential runner. Report success, LLM calls, tool calls, frozen reuse and wall time per arm as JSON + markdown under `docs/poc/`. It must run offline with `MockLLM` and live with any client.
3. Record a Decision (next number) for the OpenAI-compatible client and for the PoC metric definitions. Credit the paper (docs/ATTRIBUTION.md).

Definition of done (behavior, not tautology):
- An E2E test starts a tiny local HTTP server that speaks `/v1/chat/completions`. The first reply is malformed JSON and the second is valid. `run_task` recovers and the sink equals 25. A second test makes the server time out and expects `LLMError`, not a hang.
- The offline `poc_suite.py` shows that localized repair uses fewer LLM calls than global replan at equal success, asserted on the report.
- `uv run pytest -q -m "not integration"` is green. Report the new count.
- Live (only if `ollama ps` is empty and MemAvailable ≥ 45 GiB; never while another bench runs): `toy_parallel.py --live --model qwen2.5:14b --only`, then `qwen3.6:35b`. Optionally run against llama-server `--no-mmap` via `--client openai`. Exit code and stderr go into Decision 0017's revisit note. A skipped live run is recorded as skipped, not as a pass.
- No new hard dependencies. Core stays free of LangGraph, DSPy and NetworkX. Do not implement `escalate_after` (OQ-0016).

Handoff: write `docs/ops/HANDOFF-poc-<date>.md` (what landed, commands, measured numbers, what is still open, next step) and update docs/NEXT.md.

PR: commit on `build/atg-poc`, `git push -u origin build/atg-poc`, write the PR body to `/tmp/pr-atg-poc.md` (summary, test evidence, live result or skip reason, risks). Open the PR with `gh pr create --body-file` if gh is authenticated. Otherwise print `https://github.com/themark-net/atg-framework/compare/main...build/atg-poc?expand=1` and leave the body file path in the handoff.
Gates: do not merge. Tester and Reviewer gate the merge. Do not post on X. Do not edit pfy-mentat from this session.
