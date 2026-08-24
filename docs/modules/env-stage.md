# Module: `scripts/env-stage.sh`

**Purpose:** Product lever 2. Structural eval + optional local OpenAI-compat liveness. **Honest skip** if a piece is missing; does not fail the whole operator env.

## Entry

```bash
./pfy stage          # make env-stage
./pfy start          # runs env-stage after inference
bash scripts/env-stage.sh
```

Probes :1919, :9292, :8080, :11435, :11434 in that spirit; if only Ollama is up it may try `make smoke-litellm-ollama` and soft-skip.

## Not yet

- Failing the operator env when local inference is absent
- Requiring agent-cage for stage to succeed
