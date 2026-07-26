#!/usr/bin/env bash
# T-0091 4b: agent runner smoke (mock by default — no cloud).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=python.sh
source "$EDGE/python.sh"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
FAIL=0

ok() { printf '  OK  %s\n' "$*"; }
bad() { printf '  FAIL %s\n' "$*" >&2; FAIL=1; }

echo "== voice-agent-runner smoke (T-0091 4b) =="
echo "  MODE=mock (set VOICE_AGENT_SMOKE_REAL=1 to try grok -p)"

mkdir -p "$OUT"
# seed a prompt
"$VOICE_PY" "$EDGE/stt_edge.py" --backend text \
  --text "Reply with VOICE_4B_SMOKE_OK and do not use tools." \
  --target monitor --out-dir "$OUT" >/dev/null

echo "==> mock run"
if ! "$VOICE_PY" "$EDGE/agent_runner.py" --mode mock --out-dir "$OUT" --repo "$ROOT" \
  --prompt-file "$OUT/agent-prompt.md" --target monitor; then
  bad "mock runner exit non-zero"
else
  ok "mock runner"
fi

if grep -q VOICE_RUNNER_MOCK_OK "$OUT/last-run.json" 2>/dev/null \
  || grep -q mock "$OUT/last-run.json" 2>/dev/null; then
  ok "last-run.json has mock result"
else
  bad "last-run.json missing mock markers: $(head -c 200 "$OUT/last-run.json" 2>/dev/null)"
fi

status=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json'))['status'])")
if [[ "$status" == "done" ]]; then
  ok "status=done"
else
  bad "status=$status"
fi

echo "==> status CLI"
"$VOICE_PY" "$EDGE/agent_runner.py" --status --out-dir "$OUT" | head -15 >/dev/null
ok "status CLI"

if [[ "${VOICE_AGENT_SMOKE_REAL:-0}" == "1" ]] && command -v grok >/dev/null 2>&1; then
  echo "==> real grok -p (short)"
  if "$VOICE_PY" "$EDGE/agent_runner.py" --mode grok --out-dir "$OUT" --repo "$ROOT" \
    --transcript "Reply with exactly: VOICE_4B_REAL_OK. Do not use tools." \
    --target monitor --max-turns 2 --timeout 90; then
    ok "real grok runner"
  else
    bad "real grok runner failed (auth/network?)"
  fi
else
  ok "skip real grok (VOICE_AGENT_SMOKE_REAL!=1 or no grok)"
fi

# remote hook: VOICE_AUTO_AGENT=mock should queue
echo "==> remote auto-agent mock hook"
export VOICE_AUTO_AGENT=mock
PORT="${VOICE_REMOTE_SMOKE_PORT:-18789}"
TOKEN="agent-smoke-$RANDOM"
"$VOICE_PY" "$EDGE/remote_server.py" --host 127.0.0.1 --port "$PORT" --token "$TOKEN" --out-dir "$OUT" \
  >/tmp/voice-agent-remote.log 2>&1 &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 20); do
  curl -sS -m 1 "http://127.0.0.1:$PORT/ping" 2>/dev/null | grep -q pong && break
  sleep 0.2
done

BODY=$(curl -sS -m 30 -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"mock auto agent please","target":"monitor"}' \
  "http://127.0.0.1:$PORT/api/text")
if echo "$BODY" | grep -q '"agent_queued"'; then
  ok "api/text reports agent_queued"
else
  # may be agent_queued true/false field
  if echo "$BODY" | grep -q 'agent'; then
    ok "api/text agent field present"
  else
    bad "api/text missing agent queue info: $(echo "$BODY" | head -c 180)"
  fi
fi

# wait for mock run
for _ in $(seq 1 30); do
  st=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('status',''))" 2>/dev/null || echo "")
  [[ "$st" == "done" || "$st" == "error" ]] && break
  sleep 0.2
done
st=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('status',''))")
if [[ "$st" == "done" ]]; then
  ok "auto-agent finished status=done"
else
  bad "auto-agent status=$st"
  tail -20 /tmp/voice-agent-remote.log 2>/dev/null || true
fi

# last-run endpoint
LR=$(curl -sS -m 5 -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PORT/api/last-run")
if echo "$LR" | grep -q '"status"'; then
  ok "GET /api/last-run"
else
  bad "last-run endpoint: $LR"
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "voice-agent smoke: FAIL" >&2
  exit 1
fi
echo "voice-agent smoke: PASS"
echo "Live: VOICE_AUTO_AGENT=1 make voice-remote   # then speak/text; grok runs with tools"
exit 0
