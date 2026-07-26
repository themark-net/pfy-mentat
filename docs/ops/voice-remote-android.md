# Remote Android → host STT → tool-capable agent (T-0091 p4a)

**Status:** Implemented edge · not full VoIP  
**Depends:** Phase 1 local STT (`make voice-stt-install`) · OQ-0010 path A  
**Not:** Grok mobile voice (no tools) · Hermes primary · open internet agent phone

## Goal

Speak on **Android**, process STT on **lab host**, land a **Grok/OpenCode prompt with tools** — same handoff as desk `make voice-listen`.

```text
  Android Chrome
       │  MediaRecorder (webm)
       │  HTTPS/HTTP over Tailscale (preferred)
       ▼
  host remote_server.py :8787
       │  faster-whisper (.venv)
       ▼
  .generated/agent-prompt.md + handoff.sh + inbox/
       │
       ▼
  host: handoff.sh → grok (tools)  or  opencode worker
```

## One-time host setup

```bash
make voice-stt-install          # if not already
# Tailscale on host + phone (recommended) — same tailnet
```

## Run the remote edge

```bash
# Localhost only (test from same machine browser)
make voice-remote

# Reachable from Android on tailnet / LAN (still require token)
VOICE_REMOTE_HOST=0.0.0.0 make voice-remote
```

Token is auto-created at:

`examples/voice-stt-edge/.generated/remote.token` (gitignored, mode 600)

Print/copy into the phone UI.

### Android steps

1. Join **Tailscale** (or same LAN; Tailscale preferred).
2. Open `http://<host-tailscale-name-or-100.x-ip>:8787/` in Chrome.
3. Paste **token**.
4. Target: **monitor** (Grok tools) or **worker**.
5. Record → **Stop** → **Send audio → STT**.
6. On the **host**, when you want the agent to run with tools:

```bash
examples/voice-stt-edge/.generated/handoff.sh
# or
grok "$(cat examples/voice-stt-edge/.generated/agent-prompt.md)"
```

Typed text also works in the phone page (no mic).

## API (token required)

| Method | Path | Body |
|--------|------|------|
| GET | `/` | Mobile UI |
| GET | `/health` | No auth |
| POST | `/api/text` | `{"text":"…","target":"monitor"}` |
| POST | `/api/audio` | `{"audio_b64":"…","mime":"audio/webm","target":"monitor"}` |
| GET | `/api/last` | Last transcript (auth) |

Header: `Authorization: Bearer <token>` or `X-Voice-Token: <token>`.

```bash
export VOICE_REMOTE_TOKEN=$(cat examples/voice-stt-edge/.generated/remote.token)
curl -sS http://127.0.0.1:8787/health
curl -sS -H "Authorization: Bearer $VOICE_REMOTE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Run make eval-structural","target":"monitor"}' \
  http://127.0.0.1:8787/api/text
```

## Security rules

| Do | Do not |
|----|--------|
| Prefer **Tailscale** only reachability | Port-forward 8787 to the public internet |
| Keep **token** secret (phone + host) | Commit `remote.token` |
| Bind `127.0.0.1` for desk tests | Assume HTTPS without Tailscale/TLS |
| Run handoff yourself on host | Expect Grok mobile voice to get tools |

**Not in p4a:** auto-running `grok` on every upload (headless agent loop is a later, higher-risk step). Inbox files under `.generated/inbox/` accumulate prompts for you or a watcher.

## Env

| Variable | Default | Meaning |
|----------|---------|---------|
| `VOICE_REMOTE_HOST` | `127.0.0.1` | Bind address; use `0.0.0.0` on tailnet |
| `VOICE_REMOTE_PORT` | `8787` | Port |
| `VOICE_REMOTE_TOKEN` | auto file | Shared secret |
| `VOICE_STT_BACKEND` | `auto` | STT for `/api/audio` |

## Smoke

```bash
make smoke-voice-remote   # starts server briefly, /health + /api/text with mock path
```

## Later (not this slice)

| Step | Notes |
|------|-------|
| p4b | Optional host watcher: new inbox → `grok` headless with budget/exits |
| p4c | TTS reply audio back to phone |
| p4d | True VoIP / Twilio (OQ-0010 C) |
| TLS | `tailscale serve` or Caddy on tailnet |

## Related

- [voice-agent-channel.md](voice-agent-channel.md)  
- Local desk path: `make voice-listen`  
- Worker/monitor: [worker-monitor.md](worker-monitor.md)  
