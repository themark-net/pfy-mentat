#!/data/data/com.termux/files/usr/bin/bash
# Run ON Android inside Termux (not on the lab host).
# Records audio → POST to host voice-remote over Tailscale → prints transcript.
#
# Install on phone (Termux):
#   pkg install termux-api curl jq coreutils
#   # also install "Termux:API" from F-Droid / Play
#   mkdir -p ~/bin && cp termux-voice-send.sh ~/bin/ && chmod +x ~/bin/termux-voice-send.sh
#
# Configure once:
#   export VOICE_REMOTE_URL='http://100.x.y.z:8787'   # host Tailscale IP or MagicDNS name
#   export VOICE_REMOTE_TOKEN='…'                     # from host .generated/remote.token
#   # optional: echo those into ~/.voice-remote.env
#
# Use:
#   termux-voice-send.sh                 # record 6s, target=monitor
#   SECONDS=8 TARGET=worker termux-voice-send.sh
#   termux-voice-send.sh --text 'run make eval-structural'
set -euo pipefail

ENV_FILE="${VOICE_REMOTE_ENV:-$HOME/.voice-remote.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
fi

URL="${VOICE_REMOTE_URL:-}"
TOKEN="${VOICE_REMOTE_TOKEN:-}"
TARGET="${TARGET:-monitor}"
SECS="${SECONDS:-${VOICE_LISTEN_SECONDS:-6}}"
TEXT_MODE=0
TEXT_BODY=""

usage() {
  cat <<EOF
Usage: termux-voice-send.sh [--text 'phrase']
  VOICE_REMOTE_URL=http://<tailscale-host>:8787
  VOICE_REMOTE_TOKEN=<token from host remote.token>
  TARGET=monitor|worker|raw   SECONDS=6
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --text) TEXT_MODE=1; TEXT_BODY="${2:-}"; shift 2 || true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$URL" || -z "$TOKEN" ]]; then
  echo "error: set VOICE_REMOTE_URL and VOICE_REMOTE_TOKEN" >&2
  echo "  (host Tailscale IP + contents of examples/voice-stt-edge/.generated/remote.token)" >&2
  echo "  save to $ENV_FILE for reuse" >&2
  exit 2
fi
URL="${URL%/}"

echo "== termux → voice-remote =="
echo "  url=$URL target=$TARGET"

# Connectivity first (plain text — browser hang often = never reaches here)
echo -n "  ping: "
if ! curl -sS -m 5 "$URL/ping"; then
  echo ""
  echo "error: cannot reach $URL/ping over Tailscale" >&2
  echo "  on host: VOICE_REMOTE_HOST=0.0.0.0 make voice-remote" >&2
  echo "  on host: tailscale ip -4   # use that 100.x in VOICE_REMOTE_URL" >&2
  echo "  on phone: Tailscale connected? same account/tailnet?" >&2
  exit 1
fi

if [[ "$TEXT_MODE" -eq 1 ]]; then
  if [[ -z "$TEXT_BODY" ]]; then
    echo -n "text> "
    read -r TEXT_BODY
  fi
  RESP=$(curl -sS -m 120 \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(printf '%s' "$TEXT_BODY" | jq -Rs --arg t "$TARGET" '{text:., target:$t}')" \
    "$URL/api/text")
else
  if ! command -v termux-microphone-record >/dev/null 2>&1; then
    echo "error: termux-microphone-record missing" >&2
    echo "  pkg install termux-api  + install Termux:API app" >&2
    exit 2
  fi
  WAV="${TMPDIR:-/data/data/com.termux/files/usr/tmp}/pfy-voice-$$.wav"
  # termux-api: -f file -l limit seconds
  echo "  recording ${SECS}s — speak now…"
  termux-microphone-record -f "$WAV" -l "$SECS" >/dev/null
  # wait for file
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [[ -s "$WAV" ]] && break
    sleep 0.3
  done
  if [[ ! -s "$WAV" ]]; then
    echo "error: no recording at $WAV" >&2
    exit 1
  fi
  BYTES=$(wc -c <"$WAV" | tr -d ' ')
  echo "  captured $BYTES bytes → upload+STT…"
  # raw body upload (no base64 in shell — simpler/faster)
  RESP=$(curl -sS -m 300 \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: audio/wav" \
    -H "X-Voice-Target: $TARGET" \
    -H "X-Voice-Filename: phone.wav" \
    --data-binary @"$WAV" \
    "$URL/api/audio-raw")
  rm -f "$WAV" 2>/dev/null || true
fi

echo "$RESP" | jq -r '
  if .ok then
    "✅ " + .transcript + "\n\nhost handoff:\n  " + .handoff_path
  else
    "error: " + (.error // tostring)
  end
' 2>/dev/null || echo "$RESP"
