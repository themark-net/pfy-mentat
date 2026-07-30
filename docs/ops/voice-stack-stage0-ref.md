# Stage 0 voice stack references (T-0095)

**Status:** Catalog Stage 0 — **reference only** · ADR-0012 half-duplex local-first  
**Primary voice path:** `examples/voice-stt-edge/` + orchestrator (not these runtimes)

| Project | Role | Stage | Install? |
|---------|------|-------|----------|
| **Pipecat** | Real-time voice AI pipelines | I0/I1 awareness | **No** primary |
| **LiveKit** | WebRTC rooms / media | I0/I1 awareness | **No** primary |
| **freeapp / similar** | Consumer voice app patterns | I0 awareness | **No** primary |

## Why not primary

ADR-0012: half-duplex, local STT → text agent → optional short TTS later. Full duplex cloud stacks add cost, privacy surface, and ops weight without improving the worker/monitor coding loop.

## When to re-open

Only if product needs multi-party realtime audio rooms or cloud STT/TTS as a **product feature** — then new ADR, not silent promotion.
