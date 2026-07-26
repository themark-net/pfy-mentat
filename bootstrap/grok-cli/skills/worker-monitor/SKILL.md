---
name: worker-monitor
description: >
  Dual-session local worker + cloud monitor workflow. Use when the user runs
  /worker-monitor, says local worker, Ollama worker, Grok monitor, offload to
  local model, or dual-session OpenCode + Grok. Worker = OpenCode→Ollama
  LOCAL_CODER_MODEL; monitor = Grok with DoD/exits. See T-0085 /
  docs/ops/worker-monitor.md.
argument-hint: "[stage | monitor | worker]"
---

# /worker-monitor — Local worker + Grok monitor (T-0085)

**Pattern:** two terminals, one DoD. Not a multi-agent daemon.

| Role | Runtime | Model |
|------|---------|-------|
| Worker | OpenCode → Ollama | `LOCAL_CODER_MODEL` (default `deepseek-coder:6.7b`) |
| Monitor | **You (this Grok session)** | subscription |

## Modes

| Arg | Action |
|-----|--------|
| `stage` or *(default)* | Tell operator to run `make worker-stage` on host; then load brief |
| `monitor` | Assume brief exists; run monitor protocol below |
| `worker` | Print worker env instructions only (no Grok implement takeover) |

## Monitor protocol (this session)

1. Read `examples/opencode-ollama/.generated/monitor-brief.md` if present (or ask operator to run `make worker-stage`).
2. Restate product goal in one paragraph.
3. Write **DoD** (numbered pass/fail commands).
4. **Exit card** via `/agent-loops plan` (or fill exits inline).
5. Instruct worker to implement; **do not** re-implement on Grok unless escalated.
6. On each review: `git status` / `git diff --stat` (or ask operator for paste).
7. **Escalate** only after 3 identical worker failures or explicit architecture fork → then implement on Grok or `/adr` / `/oq`.
8. Finish: checklist green + `/hermes-feedback memory` if non-trivial.

## Do not

- Claim Grok is using Ollama for its own completions  
- Infinite retry on cloud after worker could handle mechanical fixes  
- Require Hermes Agent or company daemons  

## Handoffs

| Need | Next |
|------|------|
| Stage env | `make worker-stage` (host) |
| Voice → this session | `make smoke-voice-stt`; `stt_edge.py --text\|--mic --target monitor` then `handoff.sh` (T-0091 p1) |
| Loops/exits | `/agent-loops` |
| Unattended implement on Grok | `/one-shot` (costs cloud) |
| RCA | `/investigate` |
| Product simplicity | [product-operator-surface.md](../../../../docs/ops/product-operator-surface.md) |

## Attribution

T-0085 · ADR-0011 · T-0080 smoke path.
