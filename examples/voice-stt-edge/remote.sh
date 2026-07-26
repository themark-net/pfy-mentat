#!/usr/bin/env bash
# Start remote Android/Tailscale voice edge (T-0091 p4a).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=python.sh
source "$EDGE/python.sh"

HOST="${VOICE_REMOTE_HOST:-127.0.0.1}"
PORT="${VOICE_REMOTE_PORT:-8787}"
TOKEN="${VOICE_REMOTE_TOKEN:-}"

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
    echo "    copy this into the phone UI (once):"
    echo "    $TOKEN"
  fi
fi

if [[ ! -x "$EDGE/.venv/bin/python" ]]; then
  echo "error: run make voice-stt-install first (STT venv)" >&2
  exit 2
fi

echo "== voice-remote =="
echo "  For Android over Tailscale:"
echo "    1) Install Tailscale on phone + this host; same tailnet"
echo "    2) VOICE_REMOTE_HOST=0.0.0.0  (or your 100.x tailscale IP)"
echo "    3) Phone browser: http://<tailscale-host-name-or-ip>:$PORT/"
echo "    4) Paste token; record; Send audio"
echo "    5) On host: $EDGE/.generated/handoff.sh"
echo ""

exec "$VOICE_PY" "$EDGE/remote_server.py" --host "$HOST" --port "$PORT" --token "$TOKEN"
