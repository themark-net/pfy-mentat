# 009-voice-last-run

Structural scorer for `examples/voice-stt-edge/.generated/last-run.json`.

## Required (status=done)

```json
{
  "status": "done",
  "ok": true,
  "mode": "mock|recipe|opencode|opencode-ollama|ollama|grok",
  "long_task": true
}
```

`long_task` is optional but recommended. In-flight statuses (`running`/`queued`/`busy`)
and `error`/`skipped`/`none` are valid with matching `ok` semantics.

Related: agent_runner.py, remote GET /api/last-run, voice-clean.
