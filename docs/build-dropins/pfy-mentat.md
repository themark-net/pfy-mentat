# Build drop-in: pfy-mentat, local-model lane + ATG probe

Paste everything below the line into Grok Build on nimo.

---
Repo: `~/DEVELOP/pfy-mentat` (GitHub themark-net/pfy-mentat). Read AGENTS.md, docs/DESIGN.md, docs/adr/README.md, docs/TODO.md, docs/PENDING-HANDOFF.md, docs/eval/ATG-FRAMEWORK-EVAL.md, docs/eval/TOOLSET-RANKING.md, docs/dogfood/LOCAL-BENCH-4-EDGE.md.
Worktree: `git fetch && git worktree add tmp/build-local-lane -b build/local-lane-atg origin/main`. Never commit in the founder checkout.

Goal: make the local models first-class pfy lanes and give atg-framework a measured probe, without making ATG a pipeline dependency.

Build:
1. **llama-server lane.** Promote `pipelines/dogfood/local-bench-4/run_nommap_server.sh` into a named lane (`llamacpp-nommap`) in `data/eval-lanes.json` + `pfylib/hedge.py`. It needs start, health (`/v1/models`), stop and model path. The default model stays `qwen3.6:35b` on Ollama. `qwen3-coder-next` is opt-in via this lane. Refuse to start when MemAvailable < size + 25 GiB, and exit 2 with a reason.
2. **atg-compile bench.** New case set `data/decision-gates/atg-compile.cases.v0.json` (~10 tasks). The runner reuses `examples/local-bench/bench.py` patterns (PeakSampler, receipt, one model at a time) and calls atg-framework by path (`ATG_REPO=~/DEVELOP/atg-framework`, pinned SHA recorded in the receipt). Metrics: valid-DAG rate, sink-correct rate, repairs used, wall time. Exit 2 when atg or the endpoint is missing.
3. **Catalog card refresh** per atg `docs/ops/pfy-mentat-handoff.md`: TOOLS.md ATG row, `data/tool_integration_stages.json` (drop "No runnable core", record the SHA and gate table), `docs/ops/atg-coupling.md`. Add the missing `data/tools.json` object (triple-write). Stage stays **I1** unless a live atg-compile run on a local model passes. Then propose I2 in the PR. Do not self-promote.

Definition of done (behavior and fail-and-recover):
- An E2E test runs the bench against a fake OpenAI-compatible server that returns one malformed and one valid DAG. The receipt shows 1 valid / 1 invalid and the run exits 0.
- A test with the lane endpoint down: the bench exits 2 with a "next step" message, writes no receipt claiming a pass, and leaves no orphan process.
- A test where the memory floor refuses `llamacpp-nommap` start (inject a fake MemAvailable reading).
- `make eval-structural` and the existing tests stay green.
- Live run only on a quiet host (no other bench, `ollama ps` empty): `qwen3.6:35b`, then coder-next via the lane. Results go in `docs/dogfood/ATG-COMPILE-RESULTS.md` + `sources/entries/<next>-atg-compile.md`.

Handoff: prepend a dated section to docs/PENDING-HANDOFF.md and update the TODO row. Not a Feature GO.
PR: push `build/local-lane-atg` and write the PR body to `/tmp/pr-pfy-local-lane.md`. Use `gh pr create --body-file` if authenticated, otherwise print the compare URL and record it in the handoff.
Gates: do not merge. Tester and Reviewer gate the merge. Leave catalog HOLD 70–75 and the eval-harness untouched. Load only one model at a time.
