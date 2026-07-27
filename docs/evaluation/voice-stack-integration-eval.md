# Voice stack integration evaluation (post heavy-worth-300)

**When:** 2026-07-27 · **SHA base:** `88124b3` + follow-on eval commits  
**Scope:** Installable half-duplex voice → agent path (ADR-0012), not full-duplex media  
**Method:** Integration map + structural rubric expansion + industry research (no operator questions)

## Executive scorecard

| Layer | Grade | Notes |
|-------|-------|-------|
| **L0 Deterministic contracts** | **A−** | Install + mock 008 + recipe e2e + remote free-port + structural; now **009 last-run** + surface gate |
| **L1 Mode routing / local-first** | **B+** | Code correct (`1`→opencode); docs were stale (fixed); defaults now worker/long-task on remote |
| **L2 Real local agent quality** | **C+** | Soft-optional CI; OpenCode success is loose; tools-model path exists but not hard-gated on task success |
| **L3 STT accuracy / real mic** | **C** | Probe soft; no WER fixture; real path works on host but unmeasured |
| **L4 Task completion under tools** | **D+ / deferred** | Recipe proves *wiring* develop-loop, not LLM tool-use coding quality |
| **L5 Full-duplex / S2S** | **N/A (reject)** | ADR-0012 + research: wrong product/cost class for this lab |

**Bottom line:** The **installable spine is production-ready for operators**. The **evaluation hole** is not “missing Pipecat” — it is **weak measurement of real tool-using local agents** after STT. Next investment should deepen **L2/L4 rubrics**, not duplex media.

---

## Integration map (compressed)

```text
mic/file/Termux/text
        → stt_edge (Whisper local)
        → agent-prompt.md + handoff.sh
        → agent_runner (mock|recipe|opencode→Ollama|grok)
        → last-run.json + last-reply.txt
        → 008 receipt · 009 last-run · eval-structural · voice-clean
```

| Boundary | Contract strength | Test |
|----------|-------------------|------|
| STT wiring | Strong (mock/text) | `smoke-voice-stt` |
| Mode map 1→opencode | Strong | smoke-agent + structural `voice_operator_surface` |
| Mock long-task receipt | Strong | 008 fixtures + install + voice-clean |
| last-run.json | **Strong (new)** | **009** fixtures + e2e/CI |
| Recipe develop-loop | Strong (wiring only) | `voice-agent-e2e` |
| OpenCode/Ollama real | Soft | smoke soft-skip; CI optional soft |
| Remote HTTP + free port | Strong | smoke-remote + smoke-agent auto-queue |
| Grok escalate | Untested in CI (by design) | manual |
| Real STT WER | Missing | — |

Full boundary table: exploration session notes (agent map 2026-07-27).

---

## Rubric before → after this eval

| Was | Gap | Now |
|-----|-----|-----|
| 008 shape-only STATUS/DOD/EXIT/NEXT | Thin DOD, bad STATUS, placement | Stricter 008 + more fail fixtures |
| No last-run schema | UI/CI poll informal | **009-voice-last-run** |
| No structural install-path gate | Files could vanish green | **voice_operator_surface** check |
| Docs: `VOICE_AUTO_AGENT=1` = Grok | Cost/operator trap | Fixed to OpenCode-first |
| Remote default target **monitor** | Cloud bias | Default **worker** + long-task on when auto-agent |
| STT CLI default **monitor** | Same | Default **worker** |

### What the rubric still does **not** claim

- Agent *actually* completed multi-step software work under a real model  
- STT word error rate  
- Tool-call correctness / file-edit success rate  
- Latency / barge-in (full-duplex metrics — out of scope)

---

## Research: right path forward (not asking operator)

### 1. Industry voice eval is mostly full-duplex S2S — wrong yardstick

- **τ-voice** (Sierra, 2026): full-duplex customer-service agents; task completion ~30%→67%; retains ~79% of *text* capability. Explicitly **not** half-duplex turn-based coding.  
- Cekura / Hamming / ElevenLabs pillars: WER, TTFT, barge-in, tool/task completion, safety — useful **catalog of dimensions**, but duplex-native.  
- **Implication for pfy-mentat:** Score **text-agent task completion + optional STT WER**, not barge-in. ADR-0012 remains correct: half-duplex local STT → local coder is the sustainable product.

### 2. Local coding agents bottleneck is tool-use, not STT

- Local OpenCode + Ollama works for bulk, but community consensus (Raschka 2026, HN, OpenCode guides): **tools-capable models + large enough `num_ctx`** matter more than UI polish.  
- Chat-only fallback (Ollama HTTP without tools) cannot prove “develop software under voice.”  
- **Implication:** L4 eval must use **OpenCode with LOCAL_TOOLS_MODEL** (or grok escalate), not recipe mock alone. Soft-optional CI is right for missing models; **hard score when model present** is the next step.

### 3. Eval ladder to adopt (recommended)

| Tier | Name | Gate | Cost | Status |
|------|------|------|------|--------|
| **S0** | Structural contracts | `make eval-structural` (003–009 + surface) | $0 | **shipped** |
| **S1** | Install + mock long-task | `install-voice-agent` / voice-clean | $0 | **shipped** |
| **S2** | Soft real local reply | optional Ollama long-task | local GPU | **shipped soft** |
| **S3** | Hard real receipt when model present | if model: must pass 008 **or** explicit SKIP with reason in artifact | local | **TODO T-0097** |
| **S4** | Tool-use microtask | OpenCode edits fixture file under timed prompt; verify content + structural | local | **TODO T-0098** |
| **S5** | STT fixture WER | known wav → expected transcript (CER/WER threshold) | host | **TODO T-0099** |
| **S6** | Grok escalate smoke | `VOICE_AUTO_AGENT=grok` dry path with always-approve, max-turns=2 | cloud | **TODO T-0100** (opt-in CI) |
| **S7** | Full duplex | Pipecat/LiveKit | high | **reject as primary** (catalog only T-0095) |

### 4. What **not** to do next

- Do **not** rebuild primary stack on Pipecat/LiveKit/GPT-Realtime for “real voice agent” status. Research shows that measures a different product (duplex CS agents).  
- Do **not** treat recipe e2e as proof of coding quality.  
- Do **not** hard-fail CI when Ollama is empty — keep soft-optional for model presence.

---

## Integration findings (priority)

### Fixed in this eval pass

1. Stale **Grok-as-default-auto-agent** docs/UI copy  
2. Remote/STT defaults → **worker** local-first  
3. Remote auto-agent **defaults VOICE_LONG_TASK=1** (disable with `=0`)  
4. Rubric: **008 tighten**, **009 last-run**, **voice_operator_surface**

### Remaining P1 (implement next sessions)

| ID | Item | Why |
|----|------|-----|
| T-0097 | When Ollama model present, hard-fail optional long-task if reply fails 008 **unless** labeled SKIP | Closes “green forever with garbage LLM receipts” |
| T-0098 | Tool-use microtask eval (OpenCode + LOCAL_TOOLS_MODEL → known file edit) | Only real measure of “develop under voice” |
| T-0099 | Optional STT WER fixture (small wav in repo or generate) | Separates STT quality from agent quality |
| T-0101 | Tighten OpenCode `ok` semantics (non-zero + short text = fail) | Reduces false `last-run.ok` |

### P2 polish

- Whisper default messaging (`base` vs `base.en`)  
- Concurrent REPL+remote lock UX  
- Optional short local TTS (T-0094) for “agent done” — after L4  
- Catalog Stage 0 duplex refs only (T-0095)

---

## Component grades (detailed)

| Component | Grade | Evidence |
|-----------|-------|----------|
| `stt_edge.py` | B+ | Strong wiring; default now worker; real STT host-proven, unmeasured WER |
| `agent_runner.py` | B+ | Modes complete; long-task real; OpenCode ok-looseness is the weak joint |
| `remote_server.py` | B+ | Free-port, TLS help, auto-agent; defaults aligned |
| `install-voice-agent.sh` | A | Full gate; CI spine |
| `voice-repl.sh` | A− | Good daily path; soft 008 |
| `make/voice.mk` + Makefile include | A | Operator surface clear |
| `voice-clean.yml` | A− | Self-hosted green; soft optional local |
| 008 scorer | A− | Expanded |
| 009 scorer | A | New contract |
| OpenCode/Ollama tools path | C+ | T-0093 select exists; no task-success gate |
| Grok escalate | B (design) / untested CI | Correct cost posture |
| Docs ops set | B+ | Install one-screen + fixes this pass |

---

## Operator-facing truth (after this eval)

```bash
make voice-agent-install          # S0+S1
make voice-repl                   # daily text
VOICE_TEXT='…' make voice-agent-run
VOICE_AUTO_AGENT=1 make voice-remote   # = opencode local + long-task default
VOICE_AUTO_AGENT=grok make voice-remote  # paid escalate
make eval-structural              # includes 003–009 + voice surface
```

---

## Links

- ADR-0012 · [voice-agent-install.md](../ops/voice-agent-install.md) · [voice-agent-runner.md](../ops/voice-agent-runner.md)  
- Tasks: `examples/eval-harness/tasks/008-voice-receipt`, `009-voice-last-run`  
- Research anchors: τ-voice / Sierra 2026 (full-duplex CS); local OpenCode+Ollama tool-use literature (2026)
