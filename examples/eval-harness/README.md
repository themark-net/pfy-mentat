# Eval harness (OQ-0002 option 5 + v0.2)

**Status:** T-0003 MVP + **T-0041 v0.2**  
**Decision:** [OQ-0002](../../docs/open-questions/OQ-0002-eval-harness-shape.md) — **option 5**

| Tier / mode | Meaning | Command |
|-------------|---------|---------|
| **0** | Connectivity smoke | `make eval-tier0` → `smoke-litellm-ollama` |
| **1** | One scored coding task | `make eval-tier1` (`EVAL_TASK`) |
| **MVP** | tier0 + tier1 | `make eval-mvp` |
| **Suite (v0.2)** | All tasks, one gate model | `make eval-suite` |
| **Matrix (v0.2)** | Tasks × models | `make eval-matrix` |
| **v0.2 ladder** | tier0 + suite | `make eval-v02` |
| **Later** | DSPy + MCP | Deferred |

## Tasks

| ID | Type | What |
|----|------|------|
| `001-is-palindrome` | implement | `is_palindrome(s)` exact reverse, case-sensitive |
| `002-fix-sum-evens` | fix | Correct bug: sum **even** numbers, not odds |

Hidden tests score **pass/fail**. Path: LiteLLM → host Ollama (same as litellm smoke).

## Models

| Knob | Default | Role |
|------|---------|------|
| `LITELLM_SMOKE_MODEL` | `deepseek-coder:latest` | Tier-0 connectivity only (tiny OK) |
| `EVAL_MODEL` / `EVAL_GATE_MODEL` | `qwen2.5:14b` | Must pass for suite/matrix exit 0 |
| `EVAL_MODELS` | `qwen2.5:14b,codestral:22b,deepseek-coder:6.7b-instruct` | Matrix columns; missing → **SKIP** cell |

Tiny `deepseek-coder:latest` (~1B) is unreliable for scored tasks.

## Run

```bash
export PATH="$HOME/.local/bin:$PATH"
./examples/litellm-ollama/host-ollama-gateway.sh start
make local-ollama-up          # if needed

make eval-mvp                 # tier0 + one task
make eval-v02                 # tier0 + all tasks (gate model)
make eval-matrix              # multi-model table → pipelines/eval/results.latest.md

# overrides
make eval-tier1 EVAL_TASK=002-fix-sum-evens
make eval-suite EVAL_MODEL=codestral:22b
make eval-matrix EVAL_MODELS=qwen2.5:14b,qwen2.5-coder:7b-instruct EVAL_GATE_MODEL=qwen2.5:14b
```

## Layout

```
examples/eval-harness/
  README.md
  pins.env
  run_scored_task.py    # single task
  run_suite.py          # multi-task / multi-model
  run-in-cage.sh        # cage entry (EVAL_MODE=single|suite|matrix)
  tasks/001-is-palindrome/
  tasks/002-fix-sum-evens/
pipelines/eval/
  results.latest.md
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Gate model passed required tasks |
| 1 | Fail (score or tool error) |
| 2 | Skip (e.g. gate model missing on Ollama) |

## Non-goals

- DSPy optimizers  
- Cloud-required scoring (local Ollama only)  
- Auto catalog write into `TOOLS.md` (manual re-score still)  
