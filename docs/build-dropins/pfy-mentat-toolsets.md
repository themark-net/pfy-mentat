# Build drop-in: pfy-mentat, next toolsets (ranking #3, #4, #5, #7, #8)

Paste everything below the line into Grok Build on nimo. Run it **after** [pfy-mentat.md](pfy-mentat.md) (llama-server lane + atg-compile bench), or at the same time if you skip the parts that load models. Source: [docs/eval/TOOLSET-RANKING.md](../eval/TOOLSET-RANKING.md).

---
Repo: `~/DEVELOP/pfy-mentat` (GitHub themark-net/pfy-mentat). Read AGENTS.md, TOOLS.md, docs/eval/TOOLSET-RANKING.md, data/tool_integration_stages.json, data/toolsets.json, docs/dogfood/LOCAL-BENCH-4-EDGE.md, and sources/entries 041, 049, 051, 069.
Worktree: `git fetch && git worktree add tmp/build-toolsets -b build/toolsets-next origin/main`. Never commit in the founder checkout. Vendored code goes under `_vendor/` (git-exempt). Temp files go in /tmp or `tmp/build-toolsets/tmp`.

Goal: integrate the next five toolsets, ranked by local-only value. Each one is a separate commit and moves up exactly one integration stage. Stop after any item whose stage gate fails, record why, and move on to the next. Local models only (Ollama `qwen3.6:35b` by default). No paid keys.

Items, in order:
1. **destructive_command_guard (S).** Wire it next to write-guard for the unattended worker surfaces (`worker-monitor`, OpenCode + Ollama). The default policy blocks `rm -rf` outside the worktree, `git push --force`, `git reset --hard` on shared branches, and `dd`/`mkfs`. Target I2.
2. **Bumblebee (S).** Add it as a read-only cage probe over `_vendor/*` and the MCP configs. Make it a `make` target that writes a receipt. Target I1 → I2.
3. **DSPy on the #230 decision bench (M).** Tune the prompt and few-shot set for `qwen3.6:35b` on the 48 cases. Use a fixed held-out split (32 train / 16 test, seed recorded) and LiteLLM `ollama_chat/qwen3.6:35b`. Report accuracy, escalate rate, wrong-but-confident and parse_ok before and after on the held-out 16 only. Promote the tuned prompt only if held-out wrong-but-confident does not rise and accuracy is up by 4 points or more. Otherwise, commit the result as a negative finding. Loads one model, so it needs a quiet host.
4. **opencode-mem (S–M).** Persistent memory for the OpenCode + Ollama worker, using a local vector DB only. Store it under the worktree's tmp or `~/.local/share`, never in the repo. Target I1 → I2.
5. **llama.cpp ngram-mod speculative decoding (S).** Add it as an opt-in flag on the llama-server lane, if that lane exists (from pfy-mentat.md); otherwise skip it and note the dependency. Measure decode tok/s on 5 repetitive code-edit prompts with it on vs off. Keep it only if the speedup is 15% or more with identical outputs.

For each item update TOOLS.md, `data/tool_integration_stages.json` and `data/tools.json` (triple-write), and add `sources/entries/<next>-<slug>.md`. Never self-promote past the stage you proved.

Definition of done (behavior and fail-and-recover, no tautological units):
- dcg: an E2E test where the worker tries `rm -rf ../` and `git push --force`. Both are blocked with a reason, the worker continues, and the receipt logs the block. A second test with the guard config missing must fail closed (block), not open.
- Bumblebee: a probe run against a fixture with one deliberately suspicious MCP config flags it. A clean fixture passes. If the probe binary is missing, it exits 2 with an install hint.
- DSPy: the receipt has the before/after table on the held-out split. A test with the endpoint down exits 2 with a next-step message and writes no pass receipt.
- opencode-mem: a store, restart and recall test. A test with a corrupt store recovers by rebuilding and logs it.
- ngram-mod: the receipt has on/off tok/s. A test with the lane down skips cleanly.
- `make eval-structural` and the existing tests stay green.

Rules: load only one model at a time, and only when `ollama ps` is empty and no other bench is running. If MemAvailable is below the model size plus 25 GiB, skip the live parts and say so. No system packages, services or sudo. Commit no weights, logs or per-case jsonl.
Handoff: prepend a dated section to docs/PENDING-HANDOFF.md with each item's stage reached, its evidence path and the next step, then update the TODO rows. Not a Feature GO.
PR: push `build/toolsets-next` and write the body to `/tmp/pr-pfy-toolsets.md`. Use `gh pr create --body-file` if authenticated, otherwise print the compare URL and record it in the handoff.
Gates: do not merge. Tester and Reviewer gate the merge. Leave catalog HOLD 70–75 untouched.
