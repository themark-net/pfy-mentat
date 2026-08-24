# Module: `./pfy` (`scripts/pfy`)

**Purpose:** Product door (G8 / ADR-0012). One CLI: setup, status, start/up (inference → env-stage → active harness), models inspect, harness select.

## Entry

```bash
./pfy help
./pfy setup [local-only|balanced|max-performance]
./pfy status
./pfy start [harness]
./pfy up
./pfy harness list|use <id>|show [id]
./pfy models
./pfy models pull <name>    # Ollama adapter only
./pfy stage | eval | ship
```

Root `./pfy` is a thin shim to `scripts/pfy`. Detector is invoked with `bash` (git `+x` not required).

## Not yet

- Health-wait + default-model complete for Ollama (`./pfy start` still fire-and-forget serve)
- Remaining harness adapters (hermes, claude-code, codex, gemini, exo, continue, agent-cage)
- Treating `./pfy models` as success
