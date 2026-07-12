# Eval harness MVP (OQ-0002 option 5)

**Status:** T-0003 MVP  
**Decision:** [OQ-0002](../../docs/open-questions/OQ-0002-eval-harness-shape.md) — **option 5**

| Tier | Meaning | Command |
|------|---------|---------|
| **0** | Connectivity / install smokes (already green path) | `make eval-tier0` → `smoke-litellm-ollama` |
| **1** | One **scored** coding task in cage | `make eval-tier1` |
| **Both** | Full MVP ladder | `make eval-mvp` |
| **Later** | DSPy + MCP | Not in MVP |

## Tier 1 task: `001-is-palindrome`

Model must emit `is_palindrome(s: str) -> bool` (exact reverse, case-sensitive).  
Hidden tests score **pass/fail**. Uses LiteLLM → host Ollama (same path as litellm smoke).

**Models:** tier-0 connectivity defaults to `deepseek-coder:latest` (tiny OK).  
Tier-1 defaults to **`EVAL_MODEL=qwen2.5:14b`** — small coders often fail the scored task.

## Run

```bash
export PATH="$HOME/.local/bin:$PATH"
./examples/litellm-ollama/host-ollama-gateway.sh start
make local-ollama-up          # if needed
make eval-mvp                 # tier0 + tier1
# or:
make eval-tier0
make eval-tier1
# override scored model:
make eval-tier1 EVAL_MODEL=codestral:22b
```

## Layout

```
examples/eval-harness/
  README.md
  pins.env
  run_scored_task.py
  run-in-cage.sh
  tasks/001-is-palindrome/
    prompt.txt
    test_task.py
pipelines/eval/
  results.latest.md
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Pass |
| 1 | Fail (score or tool error) |
| 2 | Skip (e.g. model missing) |

## Non-goals (MVP)

- DSPy optimizers  
- Multi-task leaderboard  
- Cloud-required scoring (local Ollama only)  
