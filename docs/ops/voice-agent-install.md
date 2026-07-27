# Voice interactive agent — operator install (one screen)

**Product:** Edge STT + `agent_runner` (not Pipecat/LiveKit).  
**ADRs:** [ADR-0012](../adr/0012-voice-half-duplex-local-first.md) local-first · [ADR-0011](../adr/0011-hybrid-local-cloud.md) hybrid.

## Install (clone → green)

```bash
git clone <repo> && cd pfy-mentat   # tip of fix-voice-remote-port-* or main
./examples/voice-stt-edge/install-voice-agent.sh   # exits 0
# or:
make voice-agent-install
```

Proves: `eval-structural` (003–008) · STT wiring · agent smoke · mock long-task + **008-voice-receipt**.

## Daily use

| Goal | Command |
|------|---------|
| Text REPL (no mic) | `make voice-repl` |
| One long-task run | `VOICE_TEXT='fix the flaky smoke' make voice-agent-run` |
| Mock + score 008 | `make voice-agent-long-mock` |
| Deterministic e2e | `make voice-agent-e2e` |
| Desk mic (optional) | `make voice-stt-install && make voice-listen` then `make voice-agent-run` |
| Phone remote | `export VOICE_REMOTE_TOKEN=…; make voice-remote` (+ `make voice-remote-serve` for HTTPS) |

## Local vs cloud (ADR-0012)

| Env | Path |
|-----|------|
| `VOICE_AUTO_AGENT=opencode` (default bulk) | OpenCode → Ollama, or Ollama HTTP fallback |
| `VOICE_AUTO_AGENT=grok` | Grok tools (`--always-approve` when `VOICE_AGENT_ALWAYS_APPROVE=1`) |
| `VOICE_AUTO_AGENT=mock` | CI / dry-run |
| `VOICE_LONG_TASK=1` (default on REPL/run) | Multi-step DoD; final reply ends with `STATUS` / `DOD` / `EXIT` / `NEXT` |

```bash
# local bulk
VOICE_AUTO_AGENT=opencode VOICE_LONG_TASK=1 make voice-agent-run
# cloud escalate
VOICE_AUTO_AGENT=grok make voice-agent-run
```

Tools-capable local model (optional): `make eval-select-tools-model` then source `examples/opencode-ollama/.generated/tools-model.env`.

## CI (self-hosted)

Workflow: **voice-clean** (`runs-on: [self-hosted, pfy-mentat]`).

- Always: `install-voice-agent` · mock long-task + **008** + **009** · recipe e2e · free-port remote smoke · structural (incl. voice surface)
- Soft-optional: if `ollama list` shows `deepseek-coder` / `LOCAL_TOOLS_MODEL`, one bounded real local long-task; else **SKIP** (never fails for missing models)

**Eval ladder / integration scores:** [voice-stack-integration-eval.md](../evaluation/voice-stack-integration-eval.md)

```bash
# local parity
make eval-structural
./examples/voice-stt-edge/install-voice-agent.sh
make voice-agent-long-mock
make voice-agent-e2e
```

## Artifacts

Under `examples/voice-stt-edge/.generated/` (gitignored): `last-run.json`, `last-reply.txt`, `last-run.log`, `e2e-loop-marker.txt`.

## Related

- [voice-agent-runner.md](voice-agent-runner.md) · [voice-agent-channel.md](voice-agent-channel.md) · [voice-remote-android.md](voice-remote-android.md)
- Make targets: `make/voice.mk` (included from top-level `Makefile`)
