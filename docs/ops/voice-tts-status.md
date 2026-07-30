# Optional short local TTS status (T-0094)

**Not duplex.** After agent reply, optional short spoken status (e.g. “done” / “need input”).

| Item | Choice |
|------|--------|
| Primary | Piper or Kokoro **later** — install optional |
| Smoke | `make smoke-voice-tts` — probe binaries; soft-SKIP if absent |
| UAT G2 | Human listens after simple deploy |

Do not block implement-done on TTS install.
