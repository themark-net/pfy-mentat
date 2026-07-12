# Eval MVP results (OQ-0002 option 5)

| Date | Tier | Result | Task / smoke | Notes |
|------|------|--------|--------------|-------|
| 2026-07-12T02:46:31-07:00 | 1 | PASS | 001-is-palindrome | LiteLLM→Ollama scored task |
| 2026-07-12T02:47:05-07:00 | 1 | PASS | 001-is-palindrome | model=qwen2.5:14b LiteLLM→Ollama scored task |
| 2026-07-12T02:54:38-07:00 | suite | PASS | all tasks | gate=qwen2.5:14b |

### Suite/matrix 2026-07-12T09:54:37+00:00

Gate model: `qwen2.5:14b` → **PASS**

| model \ task | 001-is-palindrome | 002-fix-sum-evens | pass_rate |
|---|---|---|---|
| `qwen2.5:14b` | PASS | PASS | 2/2 |
| 2026-07-12T02:55:20-07:00 | matrix | PASS | tasks×models | gate=qwen2.5:14b models=qwen2.5:14b,codestral:22b,deepseek-coder:6.7b-instruct |

### Suite/matrix 2026-07-12T09:54:37+00:00

Gate model: `qwen2.5:14b` → **PASS**

| model \ task | 001-is-palindrome | 002-fix-sum-evens | pass_rate |
|---|---|---|---|
| `qwen2.5:14b` | PASS | PASS | 2/2 |

### Suite/matrix 2026-07-12T09:55:20+00:00

Gate model: `qwen2.5:14b` → **PASS**

| model \ task | 001-is-palindrome | 002-fix-sum-evens | pass_rate |
|---|---|---|---|
| `qwen2.5:14b` | PASS | PASS | 2/2 |
| `codestral:22b` | PASS | PASS | 2/2 |
| `deepseek-coder:6.7b-instruct` | PASS | PASS | 2/2 |
