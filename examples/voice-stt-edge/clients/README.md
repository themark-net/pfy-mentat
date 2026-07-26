# Android clients for voice-remote (over Tailscale)

The desktop browser UI is optional. **If the phone browser hangs**, use one of these instead — they talk HTTP to the same host port.

## Why the browser hangs or mic fails (usually)

| Cause | Fix |
|-------|-----|
| Host bound to `127.0.0.1` only | `VOICE_REMOTE_HOST=0.0.0.0 make voice-remote` |
| Opened `http://127.0.0.1:8787` **on the phone** | Phone must use host **Tailscale 100.x** or MagicDNS name |
| Firewall / no tailnet | Same Tailscale account; `tailscale status` green on both |
| **`getUserMedia` undefined / no Brave mic prompt** | Expected on **plain HTTP**. Use file-capture on the page, Termux, or `tailscale serve` HTTPS |
| Slow first STT after upload | Page may sit until Whisper finishes — use Termux for clearer progress |

### HTTPS for in-page browser mic

```bash
# host: voice-remote already on :8787
tailscale serve --bg --https=443 http://127.0.0.1:8787
# open the https://… URL from: tailscale serve status
```

**Connectivity test from phone (Termux):**

```bash
curl -m 5 http://100.x.y.z:8787/ping
# expect: pong
```

If `/ping` hangs, nothing else will work — fix Tailscale/bind first.

---

## Option A — Termux (recommended)

No Play “agent app” required. Reliable over Tailscale.

1. Install **Termux** + **Termux:API** (F-Droid preferred).
2. In Termux:

```bash
pkg update && pkg install termux-api curl jq coreutils
```

3. Copy `termux-voice-send.sh` from this repo onto the phone (scp, git clone of repo, or paste).

4. Config `~/.voice-remote.env`:

```bash
export VOICE_REMOTE_URL='http://100.x.y.z:8787'   # host: tailscale ip -4
export VOICE_REMOTE_TOKEN='…'                      # host .generated/remote.token
```

5. Run:

```bash
bash termux-voice-send.sh
# or text only:
bash termux-voice-send.sh --text 'run make smoke-opencode-ollama'
```

6. On host: `examples/voice-stt-edge/.generated/handoff.sh`

---

## Option B — HTTP Shortcuts (GUI, no Termux)

App: **[HTTP Shortcuts](https://http-shortcuts.rmy.se/)** (F-Droid / Play).

Create shortcut **“pfy voice text”**:

| Field | Value |
|-------|--------|
| Method | POST |
| URL | `http://100.x.y.z:8787/api/text` |
| Header | `Authorization: Bearer <token>` |
| Header | `Content-Type: application/json` |
| Body | `{"text":"{{text}}","target":"monitor"}` |
| Variable `text` | Prompt on run |

For audio, Termux is easier (file upload). HTTP Shortcuts can also POST binary if you point it at a recorded file.

---

## Option C — Desk browser (same host)

```bash
# host
VOICE_REMOTE_HOST=127.0.0.1 make voice-remote
# same machine browser
xdg-open http://127.0.0.1:8787/
```

If **this** hangs, the server is not up or port is wrong — not a Tailscale issue.

---

## Host checklist

```bash
make voice-stt-install
# print Tailscale IP
tailscale ip -4
# listen on all interfaces (required for phone)
VOICE_REMOTE_HOST=0.0.0.0 make voice-remote
# other terminal on host:
curl -sS http://127.0.0.1:8787/ping
curl -sS http://$(tailscale ip -4):8787/ping
```

Firewall (if needed): allow TCP 8787 from tailnet only (not WAN).

---

## What we are not shipping

- A Play Store “voice agent” app  
- Hermes / Telegram as required runtime (optional later)  
- Auto-run Grok on every upload without a host handoff step  

Same API either way — clients are thin; host STT + handoff stay the source of truth.
