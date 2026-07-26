# Voice STT edge → tool-capable agents (T-0091 phase 1)

**Host-only edge.** Turns speech (or pasted text) into a **transcript + agent prompt**, then hands off to:

| Target | Runtime | Tools |
|--------|---------|-------|
| `monitor` (default) | Grok Build CLI | Yes — GitHub, shell, edit |
| `worker` | OpenCode → Ollama | Partial (model-dependent) |
| `raw` | transcript only | — |

This is **not** Grok mobile voice (code stuck in chat).  
This is **not** Hermes as primary runtime (OQ-0010 path **A**: STT edge → existing agents).

## Quick start

```bash
# Lab smoke (no mic, no Whisper install)
make smoke-voice-stt

# Simulate a spoken request without STT
python3 examples/voice-stt-edge/stt_edge.py \
  --text "Run make eval-structural and fix any failures" \
  --target monitor

# Launch Grok with that prompt (tools on)
examples/voice-stt-edge/.generated/handoff.sh
# or:
grok "$(cat examples/voice-stt-edge/.generated/last-transcript.txt)"
```

## Real STT (host)

Backends (`--backend`):

| Backend | Needs |
|---------|--------|
| `mock` | Fixture only (smoke default) |
| `text` | `--text` or stdin |
| `local` / `whisper` | `pip install openai-whisper` or `faster-whisper`, or `whisper` CLI |
| `openai` | `OPENAI_API_KEY` (Whisper API) |
| `ollama` | Ollama with audio transcription API + model (experimental) |
| `auto` | Tries local → openai → ollama |

```bash
# Mic → local Whisper → Grok monitor
python3 examples/voice-stt-edge/stt_edge.py --mic --seconds 6 --backend local --target monitor
./examples/voice-stt-edge/.generated/handoff.sh

# File → cloud Whisper → worker prompt
python3 examples/voice-stt-edge/stt_edge.py --audio note.wav --backend openai --target worker
```

Mic capture uses `arecord` or `ffmpeg` when installed.

## Artifacts (gitignored)

Under `examples/voice-stt-edge/.generated/`:

| File | Role |
|------|------|
| `last-transcript.txt` | Clean spoken intent |
| `agent-prompt.md` | Wrapped prompt (role + tool instructions) |
| `handoff.sh` | Launch `grok` or `opencode` with prompt |
| `last-meta.json` | Backend/target metadata |
| `last-capture.wav` | Last mic recording (if `--mic`) |

## Env vars

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Cloud Whisper (`--backend openai`) |
| `VOICE_STT_WHISPER_MODEL` | Local model name (default `base`) |
| `VOICE_STT_OLLAMA_MODEL` | Ollama audio model (default `whisper`) |
| `OLLAMA_HOST` | Ollama base (default `http://127.0.0.1:11434`) |
| `VOICE_STT_OUT` | Override output dir for smoke |

Registered in [bootstrap/env/REGISTRY.md](../../bootstrap/env/REGISTRY.md).

## Phase map

| Phase | This package |
|-------|----------------|
| **1** (here) | STT → text → Grok/OpenCode handoff |
| 2 | TTS replies + wake word |
| 3 | Auto worksheet with worker-monitor |
| 4 | Remote Tailscale/VoIP |
| 5 | Product lever voice→stage/ship |

See [docs/ops/voice-agent-channel.md](../../docs/ops/voice-agent-channel.md).

## Related

- T-0085 worker/monitor · ADR-0011 hybrid surfaces  
- Pattern refs: Hermes voice mode, l0cut15/hermes-voice-assistant (edge only; not primary runtime)  
