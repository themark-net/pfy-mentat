#!/usr/bin/env bash
# Start remote Android/Tailscale voice edge (T-0091 p4a).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=python.sh
source "$EDGE/python.sh"

PORT="${VOICE_REMOTE_PORT:-8787}"
TOKEN="${VOICE_REMOTE_TOKEN:-}"

# Default: if Tailscale looks present and host not set, bind all interfaces
# (127.0.0.1 alone is why phone browsers hang — nothing is listening for them).
if [[ -n "${VOICE_REMOTE_HOST:-}" ]]; then
  HOST="$VOICE_REMOTE_HOST"
elif command -v tailscale >/dev/null 2>&1 && tailscale status >/dev/null 2>&1; then
  HOST="0.0.0.0"
  echo "==> Tailscale up → default VOICE_REMOTE_HOST=0.0.0.0 (phone-reachable)"
else
  HOST="127.0.0.1"
  echo "==> no Tailscale detected → bind 127.0.0.1 (desk only)"
  echo "    for phone: VOICE_REMOTE_HOST=0.0.0.0 make voice-remote"
fi

if [[ -z "$TOKEN" ]]; then
  if [[ -f "$EDGE/.generated/remote.token" ]]; then
    TOKEN="$(tr -d '[:space:]' <"$EDGE/.generated/remote.token")"
    export VOICE_REMOTE_TOKEN="$TOKEN"
    echo "==> using token from $EDGE/.generated/remote.token"
  else
    mkdir -p "$EDGE/.generated"
    TOKEN="$("$VOICE_PY" "$EDGE/remote_server.py" --generate-token)"
    printf '%s\n' "$TOKEN" >"$EDGE/.generated/remote.token"
    chmod 600 "$EDGE/.generated/remote.token"
    export VOICE_REMOTE_TOKEN="$TOKEN"
    echo "==> generated VOICE_REMOTE_TOKEN → $EDGE/.generated/remote.token"
  fi
fi

if [[ ! -x "$EDGE/.venv/bin/python" ]]; then
  echo "error: run make voice-stt-install first (STT venv)" >&2
  exit 2
fi

TS_IP=""
if command -v tailscale >/dev/null 2>&1; then
  TS_IP="$(tailscale ip -4 2>/dev/null | head -1 || true)"
fi

echo "== voice-remote =="
echo "  bind:  http://${HOST}:${PORT}/"
echo "  token: $EDGE/.generated/remote.token"
if [[ -n "$TS_IP" ]]; then
  echo "  Tailscale IPv4: $TS_IP"
  echo "  Phone URL:      http://${TS_IP}:${PORT}/ping   # must print pong"
  echo "  Phone UI:       http://${TS_IP}:${PORT}/"
fi
echo ""
echo "  Browser hangs? Prefer Termux client (no browser):"
echo "    docs: examples/voice-stt-edge/clients/README.md"
echo "    script: clients/termux-voice-send.sh"
echo "    VOICE_REMOTE_URL=http://${TS_IP:-100.x.y.z}:${PORT}"
echo "    VOICE_REMOTE_TOKEN=\$(cat $EDGE/.generated/remote.token)"
echo ""
echo "  After STT on host: $EDGE/.generated/handoff.sh"
echo ""

if [[ "$HOST" == "127.0.0.1" || "$HOST" == "localhost" ]]; then
  echo "warning: bound to localhost only — Android cannot connect." >&2
  echo "  fix: VOICE_REMOTE_HOST=0.0.0.0 make voice-remote" >&2
fi

exec "$VOICE_PY" "$EDGE/remote_server.py" --host "$HOST" --port "$PORT" --token "$TOKEN"
