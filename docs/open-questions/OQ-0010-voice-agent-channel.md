# OQ-0010: Voice channel for tool-capable agentic coding

- **Priority:** P2  
- **Status:** **resolved** (2026-07-26) → [ADR-0012](../adr/0012-voice-half-duplex-local-first.md)  
- **Blocks:** — (implementation follows ADR-0012)  
- **Related:** [voice-agent-channel.md](../ops/voice-agent-channel.md), T-0085, ADR-0011/0012

## Question

How should voice enter the stack so it has **tool use** (git, pipelines, file edit)—unlike Grok mobile voice—without forcing Hermes Agent as primary runtime?

## Branching options (historical)

| ID | Option | Outcome |
|----|--------|---------|
| A | **Voice edge only** (Whisper/TTS → existing Grok/OpenCode text) | **Chosen**, refined |
| B | Evaluate Hermes voice as optional adapter | Catalog/ref only; not primary |
| C | Telephony first | Deferred (phase 4d+) |
| D | Defer voice entirely | Rejected — half-duplex path already works |

## Resolution (operator + cost)

**Accepted path (ADR-0012):**

1. **Half-duplex** (push-to-talk / end-of-utterance) — not cloud full-duplex S2S.  
2. **Local STT** (Whisper in project `.venv`).  
3. **Default auto-agent = OpenCode → Ollama** for sustainable bulk; **Grok only opt-in** escalation (subscription cost rising).  
4. **Tailscale** for phone → host (proven).  
5. Full duplex (Pipecat/LiveKit/GPT-Live) **deferred** until local duplex is cheap or budget returns.

Rationale: full duplex burns continuous tokens/minutes on expensive cloud; X/localmaxxing setups commonly accept half-duplex + local agent. Operator prioritizes OpenCode/local over Grok-as-default for voice.

## Residual / later OQs

- Tools-capable local Ollama model for OpenCode (or explicit tool-split).  
- Optional short **local TTS** (status only), not full duplex.  
- Optional D1: Pipecat local media without cloud S2S.  
- Distillation: cloud → local coder quality (separate track).
