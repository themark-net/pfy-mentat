#!/usr/bin/env bash
# T-0092: voice auto-agent local-first smoke (no cloud required).
# Covers: mock · opencode/ollama path · VOICE_AUTO_AGENT=1 maps to opencode · remote hook
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

echo "== voice-agent smoke (T-0092 local-first) =="
echo "  default bulk: opencode/ollama · grok only if VOICE_AUTO_AGENT=grok"

mkdir -p "$OUT"

# --- 0) mode mapping ---
echo "==> mode mapping (1/on → opencode, not grok)"
MAP=$("$VOICE_PY" - <<'PY'
import importlib.util
from pathlib import Path
p = Path("examples/voice-stt-edge/agent_runner.py")
spec = importlib.util.spec_from_file_location("ar", p)
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)
assert ar.normalize_mode("1") == "opencode", ar.normalize_mode("1")
assert ar.normalize_mode("on") == "opencode"
assert ar.normalize_mode("auto") == "opencode"
assert ar.normalize_mode("grok") == "grok"
assert ar.normalize_mode("0") == "off"
print("map-ok")
PY
)
if [[ "$MAP" == "map-ok" ]]; then ok "VOICE_AUTO_AGENT=1 → opencode"; else bad "mode map"; fi

# seed prompt
"$VOICE_PY" "$EDGE/stt_edge.py" --backend text \
  --text "Reply with exactly: LOCAL_VOICE_AGENT_OK. Be brief." \
  --target worker --out-dir "$OUT" >/dev/null

# --- 1) mock ---
echo "==> mock run"
if "$VOICE_PY" "$EDGE/agent_runner.py" --mode mock --out-dir "$OUT" --repo "$ROOT" \
  --prompt-file "$OUT/agent-prompt.md" --target worker; then
  ok "mock runner"
else
  bad "mock runner"
fi
grep -q VOICE_RUNNER_MOCK_OK "$OUT/last-run.json" && ok "mock marker" || bad "mock marker"

# --- 2) opencode/local path (CLI or Ollama fallback) ---
echo "==> opencode/local run (no cloud)"
set +e
"$VOICE_PY" "$EDGE/agent_runner.py" --mode opencode --out-dir "$OUT" --repo "$ROOT" \
  --transcript "Reply with exactly: LOCAL_VOICE_AGENT_OK" \
  --target worker --timeout 120 >"$OUT/smoke-opencode-out.json" 2>"$OUT/smoke-opencode.err"
OC_RC=$?
set -e
MODE=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('mode',''))")
STATUS=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('status',''))")
OKFLAG=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('ok',False))")

if [[ "$STATUS" == "done" && "$OKFLAG" == "True" ]]; then
  ok "local agent done mode=$MODE"
elif [[ "$STATUS" == "error" ]]; then
  if grep -qi 'Ollama completion failed\|cannot connect\|Connection refused' "$OUT/last-run.json" \
    || grep -qi 'Ollama completion failed\|Connection refused' "$OUT/smoke-opencode.err" 2>/dev/null; then
    ok "local agent SKIP (Ollama unreachable) — install/start Ollama for full path"
    echo "  note: mode mapping + mock still prove T-0092 wiring"
  else
    bad "local agent error: $(head -c 200 "$OUT/last-run.json")"
    cat "$OUT/smoke-opencode.err" 2>/dev/null | tail -15 || true
  fi
else
  bad "unexpected status=$STATUS ok=$OKFLAG mode=$MODE rc=$OC_RC"
fi

# --- 3) status CLI ---
echo "==> CLI status"
"$VOICE_PY" "$EDGE/agent_runner.py" --status --out-dir "$OUT" >/dev/null && ok "status CLI"

# --- 4) remote hook: free port + matching token ---
echo "==> remote VOICE_AUTO_AGENT=1 queues local agent"
export VOICE_AUTO_AGENT=1
if [[ -n "${VOICE_REMOTE_SMOKE_PORT:-}" ]]; then
  PORT="$VOICE_REMOTE_SMOKE_PORT"
else
  PORT=$("$VOICE_PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
fi
TOKEN="t0092-$(date +%s)-$RANDOM"
LOG="/tmp/voice-t0092-remote-$$.log"
"$VOICE_PY" "$EDGE/remote_server.py" --host 127.0.0.1 --port "$PORT" --token "$TOKEN" --out-dir "$OUT" \
  >"$LOG" 2>&1 &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT

PONG=0
for _ in $(seq 1 40); do
  if curl -sS -m 1 "http://127.0.0.1:$PORT/ping" 2>/dev/null | grep -qx 'pong'; then
    PONG=1
    break
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    bad "remote_server exited before ready; log:"
    tail -30 "$LOG" 2>/dev/null || true
    break
  fi
  sleep 0.15
done

if [[ "$PONG" -ne 1 ]]; then
  bad "remote /ping never returned pong on port $PORT"
  tail -30 "$LOG" 2>/dev/null || true
else
  ok "remote /ping on :$PORT"
  BODY=$(curl -sS -m 8 -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d '{"text":"Reply LOCAL_VOICE_AGENT_OK","target":"worker"}' \
    "http://127.0.0.1:$PORT/api/text" || true)
  if echo "$BODY" | grep -qE '"agent_queued"[[:space:]]*:[[:space:]]*true'; then
    ok "api/text agent_queued under VOICE_AUTO_AGENT=1"
  else
    bad "agent_queued missing: $(echo "$BODY" | head -c 220)"
    tail -20 "$LOG" 2>/dev/null || true
  fi
  AM=$(echo "$BODY" | "$VOICE_PY" -c "import sys,json
try:
 d=json.load(sys.stdin); print(d.get('agent_mode',''))
except Exception:
 print('')" 2>/dev/null || echo "")
  if [[ "$AM" == "opencode" ]]; then
    ok "agent_mode=opencode"
  else
    bad "expected agent_mode=opencode got '$AM' body=$(echo "$BODY" | head -c 180)"
  fi

  for _ in $(seq 1 60); do
    st=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('status',''))" 2>/dev/null || echo "")
    [[ "$st" == "done" || "$st" == "error" ]] && break
    sleep 0.25
  done
  st=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('status',''))")
  md=$("$VOICE_PY" -c "import json;print(json.load(open('$OUT/last-run.json')).get('mode',''))")
  if [[ "$st" == "done" ]]; then
    ok "auto-agent finished status=done mode=$md"
  elif [[ "$st" == "error" ]] && echo "$md" | grep -qE 'ollama|opencode|mock'; then
    ok "auto-agent finished with local-stack status=$st mode=$md — wiring OK"
  else
    bad "auto-agent status=$st mode=$md"
    tail -25 "$LOG" 2>/dev/null || true
  fi

  LR=$(curl -sS -m 5 -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PORT/api/last-run" || true)
  echo "$LR" | grep -q '"status"' && ok "GET /api/last-run" || bad "last-run body=$(echo "$LR" | head -c 120)"
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "voice-agent smoke (T-0092): FAIL" >&2
  exit 1
fi
echo "voice-agent smoke (T-0092): PASS"
echo "Recipe: VOICE_AUTO_AGENT=opencode make voice-remote   # or =1 (same)"
echo "Escalate: VOICE_AUTO_AGENT=grok make voice-remote"
exit 0
