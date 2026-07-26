#!/usr/bin/env bash
# T-0091 p4a: remote voice edge smoke (host). No phone required.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=python.sh
source "$EDGE/python.sh"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
PORT="${VOICE_REMOTE_SMOKE_PORT:-18787}"
TOKEN="smoke-token-$(date +%s)"
HOST="127.0.0.1"
FAIL=0

log() { printf '==> %s\n' "$*"; }
ok() { printf '  OK  %s\n' "$*"; }
bad() { printf '  FAIL %s\n' "$*" >&2; FAIL=1; }

echo "== voice-remote smoke (T-0091 p4a) =="
echo "  MODE=localhost HTTP + /api/text (no mic, no Tailscale required)"

mkdir -p "$OUT"
# start server
"$VOICE_PY" "$EDGE/remote_server.py" --host "$HOST" --port "$PORT" --token "$TOKEN" --out-dir "$OUT" \
  >/tmp/voice-remote-smoke.log 2>&1 &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT

# wait for health
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sS -m 1 "http://$HOST:$PORT/health" >/tmp/vr-health.json 2>/dev/null; then
    break
  fi
  sleep 0.3
done

log "health"
if grep -q '"ok": true' /tmp/vr-health.json 2>/dev/null || grep -q '"ok":true' /tmp/vr-health.json 2>/dev/null; then
  ok "health"
else
  bad "health: $(cat /tmp/vr-health.json 2>/dev/null || echo none)"
  cat /tmp/voice-remote-smoke.log 2>/dev/null | tail -20 || true
fi

log "unauthorized blocked"
CODE=$(curl -sS -o /tmp/vr-unauth.json -w '%{http_code}' -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text":"nope","target":"monitor"}' \
  "http://$HOST:$PORT/api/text" || echo 000)
if [[ "$CODE" == "401" ]]; then
  ok "401 without token"
else
  bad "expected 401 got $CODE"
fi

log "text → artifacts"
CODE=$(curl -sS -o /tmp/vr-text.json -w '%{http_code}' -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Remote smoke: run make eval-structural","target":"monitor"}' \
  "http://$HOST:$PORT/api/text" || echo 000)
if [[ "$CODE" == "200" ]] && grep -q 'Remote smoke' /tmp/vr-text.json; then
  ok "api/text 200"
else
  bad "api/text code=$CODE body=$(head -c 200 /tmp/vr-text.json 2>/dev/null)"
fi

if grep -q 'Remote smoke' "$OUT/last-transcript.txt" 2>/dev/null; then
  ok "last-transcript written"
else
  bad "last-transcript missing remote text"
fi

if [[ -x "$OUT/handoff.sh" ]] && grep -q 'grok' "$OUT/handoff.sh"; then
  ok "handoff.sh ready"
else
  bad "handoff incomplete"
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "voice-remote smoke: FAIL" >&2
  exit 1
fi
echo "voice-remote smoke: PASS"
echo "Android path: docs/ops/voice-remote-android.md · make voice-remote"
exit 0
