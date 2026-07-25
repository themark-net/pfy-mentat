# OQ-0010: Voice channel for tool-capable agentic coding

- **Priority:** P2  
- **Status:** open  
- **Blocks:** T-0091 phase choices (not blocking local text worker/monitor)  
- **Related:** [docs/ops/voice-agent-channel.md](../ops/voice-agent-channel.md), T-0085, ADR-0011

## Question

How should voice enter the stack so it has **tool use** (git, pipelines, file edit)—unlike Grok mobile voice—without forcing Hermes Agent as primary runtime?

## Branching options

| ID | Option | Human decisions |
|----|--------|-----------------|
| A | **Voice edge only** (Whisper/TTS → existing Grok/OpenCode text) | Prefer local STT vs cloud STT? |
| B | **Evaluate Hermes voice** as optional adapter (not primary CLI) | Allow Hermes install in lab? |
| C | **Telephony** (Twilio/AgentPhone/VoIP) first | Accept third-party phone costs + security? |
| D | **Defer voice** until T-0090 product levers exist | — |

**Default until answered:** **A** (local STT edge → text agents), document B as catalog eval, C phase 4.

## Resolution notes

_(empty)_
