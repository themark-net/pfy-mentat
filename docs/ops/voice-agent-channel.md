# Voice channel for agentic coding (goal)

**Status:** Documented goal · not implemented  
**ID:** T-0091 · OQ-0010  
**Related:** T-0085 worker/monitor · ADR-0011 · Hermes pattern (not runtime) · T-0090 minimal levers

## Problem (operator experience)

| Surface | Voice? | Tool use / GitHub / pipelines? |
|---------|--------|--------------------------------|
| Grok **mobile voice** | Excellent UX | **No** — code stays in chat; no tools |
| Grok mobile/web **text**, Grok CLI | Typing | Yes — tools, GitHub, codegen that lands |
| Local OpenCode worker (T-0080/85) | Typing | Partial (model tools vary) |
| Desired | Phone/VoIP or hands-free voice | **Same** tools as CLI agent: edit, git, CI, iterate failures |

Voice without tools is demos. Tools without voice force keyboard. Goal = **voice I/O layer in front of a tool-capable agent**, not voice as a separate dead-end product.

## Desired architecture (layers)

```text
  Phone / VoIP / mic (local or remote)
           │
           ▼
  ┌─────────────────────┐
  │  Voice edge         │  STT (in) + optional TTS (out)
  │  Whisper / cloud STT│  low latency, optional wake word
  └──────────┬──────────┘
             │ text prompts + spoken summaries
             ▼
  ┌─────────────────────┐
  │  Agent runtime      │  tool-capable: OpenCode worker and/or Grok monitor
  │  skills + MCP + git │  same process as T-0085
  └──────────┬──────────┘
             │
             ▼
  repo · make smokes · GitHub Actions · cage
```

**Not required:** replace Grok subscription. Voice can drive **monitor** (cloud) or **worker** (local) or both via the same dual-role model.

## What worker-monitor is today (honest)

`make worker-stage` + two terminals is a **human-mediated handoff**, not automatic task routing:

| Works | Does not |
|-------|----------|
| Shared DoD file + exit card | Automatic “assign ticket to worker” |
| Worker implements on Ollama | Shared live context without paste |
| Monitor reviews diffs | Single process voice→tools |
| Escalation after 3 fails (process) | Phone call into the agent |

So: **useful scaffold**, not yet “hands-free agentic coding.” Gaps: shared state bus, tool-capable local models (or tools always on monitor), voice edge, remote access (Tailscale/VoIP).

## Building blocks found (post-doc research)

### Already in *this* catalog

| Item | Relevance |
|------|-----------|
| Hermes **feedback loops** (Entry 048) | Patterns only (`/hermes-feedback`) — **not** voice |
| awesome-hermes-skills (053) | Skills library — no voice channel scored |
| Worker/monitor (T-0085) | Dual session for local/cloud — **text** |
| Grok CLI + GitHub MCP | Tool path for monitor |
| OpenCode + Ollama (T-0080) | Local worker path |

**No prior TOOLS.md row** for voice STT/TTS, VoIP agent gateways, or “voice → coding agent” stacks was found in-repo (X pipeline has not absorbed a dedicated voice-coding seed yet).

### External (high signal, not adopted)

| Source | What | Fit |
|--------|------|-----|
| [NousResearch/hermes-agent voice mode](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/voice-mode.md) | Voice in CLI + Telegram/Discord; live Discord VC | Closest “productized” voice+agent; **runtime** conflicts with “no Hermes primary” unless adapter-only |
| [Use Voice Mode with Hermes](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/guides/use-voice-mode-with-hermes.md) | Practical setup | Reference recipe |
| [l0cut15/hermes-voice-assistant](https://github.com/l0cut15/hermes-voice-assistant) | Local Whisper STT + Kokoro TTS → Hermes API; Docker; Tailscale note | **Best local STT/TTS edge** pattern to reuse without full Hermes UI |
| Hermes issues: Twilio skill, AgentPhone, mobile companion | Phone/SMS/VoIP tracks | Telephony = separate spike |
| OpenCode + Ollama tools | Model-dependent tools | Worker tools ≠ voice |

**Recommendation (not yet decided):**

1. **Do not** make Hermes Agent the primary runtime (ADR-0010/0011 posture).  
2. **Do** catalog Hermes voice + hermes-voice-assistant as **A/B reference**.  
3. Prefer **voice edge (STT/TTS) → our worker/monitor text agents** (OpenCode local + Grok monitor with tools/GitHub).  
4. Phone/VoIP = phase 2 after local mic loop works.

## Phased plan

| Phase | Deliverable | Success |
|-------|-------------|---------|
| **0** | This doc + OQ-0010 + T-0091 | Goal visible; no silent scope creep |
| **1** | Local mic: Whisper (or cloud STT) → text into **monitor** Grok or worker OpenCode | Spoken “run smoke / fix fail” becomes a prompt with tools |
| **2** | TTS replies + optional wake word | Hands-free loop at desk |
| **3** | Shared worksheet auto-update (worker progress → monitor brief) | Less paste between terminals |
| **4** | Remote: Tailscale / VoIP / Twilio-class | Phone while away; security review required |
| **5** | Product lever: voice as input to `stage`/`ship` | Aligns T-0090 simplicity |

## Security / non-goals

- No “disable all cage policy for voice”  
- No committing always-on open phone agents to the internet without ADR  
- Voice edge must not hold raw cloud API keys in mobile apps carelessly  
- Greenfield STT/TTS only if catalog edges fail Stage 0  

## Open questions

See **OQ-0010** (channel priority, Hermes eval depth, latency budget).

## Related

- [worker-monitor.md](worker-monitor.md)  
- [product-operator-surface.md](product-operator-surface.md)  
- Entry 048 Hermes feedback (loops only)  
