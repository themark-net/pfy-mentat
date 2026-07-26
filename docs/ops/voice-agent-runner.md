# Voice → tool-capable agent runner (T-0091 phase 4b)

**Status:** Live  
**Closes the gap:** STT file → **actual tools** without `handoff.sh`

## What it does

```text
transcript / agent-prompt.md
        │
        ▼
  agent_runner.py
        │  VOICE_AUTO_AGENT=1|mock|grok|opencode
        ▼
  grok --cwd REPO --max-turns N --always-approve \\
       --output-format plain --prompt-file …
        │
        ▼
  last-run.json · last-reply.txt · last-run.log
  (phone: GET /api/last-run)
```

## Opt-in (important) — ADR-0012

| `VOICE_AUTO_AGENT` | Behavior | Cost |
|--------------------|----------|------|
| unset / `0` | STT only — safe default | $0 |
| **`opencode`** | **Preferred bulk:** OpenCode → Ollama after STT | Local only |
| `1` / `grok` | Grok headless with tools | **Cloud — escalate only** |
| `mock` | Fake agent (smokes / dry-run) | $0 |

**Sustainable recipe (operator default under rising Grok price):**

```bash
VOICE_AUTO_AGENT=opencode VOICE_REMOTE_HOST=127.0.0.1 make voice-remote
# escalate hard problems: VOICE_AUTO_AGENT=grok for one session
```

Remote open without this flag will **not** burn cloud quota.

## Host recipes

```bash
# A) Remote phone + auto tools
VOICE_AUTO_AGENT=1 VOICE_REMOTE_HOST=127.0.0.1 make voice-remote
make voice-remote-serve   # HTTPS for mic
# speak/text on phone → tools run on host → poll last-run in UI

# B) Desk after STT
examples/voice-stt-edge/python.sh examples/voice-stt-edge/stt_edge.py \
  --text "run make eval-structural and report" --auto-agent

# C) Re-run agent on last prompt only
make voice-agent-run
# VOICE_AGENT_MODE=mock make voice-agent-run

# D) Smoke (no cloud)
make smoke-voice-agent
```

## Caps

| Env | Default | Meaning |
|-----|---------|---------|
| `VOICE_AGENT_MAX_TURNS` | `8` | Grok `--max-turns` |
| `VOICE_AGENT_TIMEOUT` | `600` | subprocess timeout (s) |
| `VOICE_AGENT_ALWAYS_APPROVE` | `1` | pass `--always-approve` |
| `VOICE_AGENT_REPO` | repo root | `--cwd` for Grok |

## Artifacts (gitignored)

| File | Role |
|------|------|
| `.generated/last-run.json` | status: queued/running/done/error |
| `.generated/last-reply.txt` | assistant text |
| `.generated/last-run.log` | full stdout/stderr |
| `.generated/last-agent-prompt.txt` | exact prompt sent |

## API

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/text` `/api/audio` | include `agent_queued` when auto on |
| GET | `/api/last-run` | auth; poll for status/reply |

## Security

- Default **off**
- Still require Tailscale + token for remote
- `--always-approve` is powerful — only on trusted host
- Do not expose runner to the public internet

## Not in 4b

- TTS of reply to phone  
- Sticky multi-session resume (use `grok -c` later)  
- Hermes primary runtime  

## Related

- [voice-agent-channel.md](voice-agent-channel.md)  
- [voice-remote-android.md](voice-remote-android.md)  
