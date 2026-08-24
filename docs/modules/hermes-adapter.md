# Module: Hermes runtime adapter

**Purpose:** Exec `hermes` or `hermes-agent` from `./pfy start hermes`. Inference via `LOCAL_OPENAI_BASE_URL` from the ADR-0014 detector (not Ollama-only). The Grok skill `/hermes-feedback` stays process-only.

## Entry

```bash
./pfy harness use hermes
./pfy start hermes
```

Detect: `hermes` or `hermes-agent` on PATH. When the local runtime is ready, `OPENAI_BASE_URL` defaults to `LOCAL_OPENAI_BASE_URL`.

Missing binary: `STUB harness: hermes`, issue #56, installer one-liner, exit 2. No fake ready.

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

Upstream: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)

## Not yet

- Changing `/hermes-feedback` (process-only pattern port)
- Vendoring Hermes into git
- Other harness adapters
