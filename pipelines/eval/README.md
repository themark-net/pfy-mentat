# Eval pipeline (structural + MVP + v0.2)

See [examples/eval-harness/](../../examples/eval-harness/).

```bash
make eval-structural   # design/coding gates, NO LLM → structural.latest.md
make eval-mvp          # tier0 + one task (needs Ollama gateway)
make eval-v02          # tier0 + all implement tasks (gate model)
make eval-matrix       # tasks × models → results.latest.md
```

Lanes: [`data/eval-lanes.json`](../../data/eval-lanes.json).
