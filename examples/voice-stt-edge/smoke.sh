#!/usr/bin/env bash
# T-0091 phase 1: voice STT edge smoke (host). No mic / no Whisper required.
#
# Proves:
#   1. stt_edge.py runs (mock + text backends)
#   2. Artifacts: last-transcript.txt, agent-prompt.md, handoff.sh, last-meta.json
#   3. Prompt is wrapped for monitor (tools language) and worker targets
#   4. Optional: real STT backend probe (SKIP, not FAIL, if missing)
#
# Exit: 0 PASS · 1 FAIL
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
RESULT_MD="${VOICE_STT_RESULT:-$ROOT/pipelines/smoke/voice-stt-edge/results.latest.md}"
PY="${PYTHON:-python3}"
FAIL=0

log() { printf '==> %s\n' "$*"; }
ok() { printf '  OK  %s\n' "$*"; }
bad() { printf '  FAIL %s\n' "$*" >&2; FAIL=1; }

echo "== voice-stt-edge smoke (T-0091 p1) =="
echo "  OUT=$OUT"

mkdir -p "$OUT" "$(dirname "$RESULT_MD")"
rm -f "$OUT/last-transcript.txt" "$OUT/agent-prompt.md" "$OUT/handoff.sh" "$OUT/last-meta.json"

# --- 1) CLI exists ---
log "CLI present"
if [[ ! -f "$EDGE/stt_edge.py" ]]; then
  bad "missing $EDGE/stt_edge.py"
  exit 1
fi
ok "stt_edge.py"

# --- 2) mock backend → monitor wrap ---
log "mock backend → monitor prompt"
if ! "$PY" "$EDGE/stt_edge.py" --backend mock --target monitor --out-dir "$OUT" >"$OUT/smoke-stdout.txt"; then
  bad "mock backend failed"
else
  ok "mock run"
fi

if [[ ! -s "$OUT/last-transcript.txt" ]]; then
  bad "last-transcript.txt missing/empty"
else
  if grep -qi 'smoke-opencode-ollama' "$OUT/last-transcript.txt"; then
    ok "transcript has fixture intent"
  else
    bad "transcript missing expected fixture phrase"
  fi
fi

if [[ ! -s "$OUT/agent-prompt.md" ]]; then
  bad "agent-prompt.md missing"
else
  for needle in "Voice → agent prompt" "Spoken intent" "tools" "monitor"; do
    if grep -qi "$needle" "$OUT/agent-prompt.md"; then
      ok "prompt contains: $needle"
    else
      bad "prompt missing: $needle"
    fi
  done
fi

if [[ ! -x "$OUT/handoff.sh" ]]; then
  bad "handoff.sh missing or not executable"
else
  if grep -q 'grok' "$OUT/handoff.sh" && grep -q 'opencode' "$OUT/handoff.sh"; then
    ok "handoff.sh mentions grok + opencode"
  else
    bad "handoff.sh incomplete"
  fi
fi

if [[ ! -s "$OUT/last-meta.json" ]]; then
  bad "last-meta.json missing"
else
  ok "last-meta.json"
fi

# stdout should be clean transcript only
if grep -qi 'smoke-opencode-ollama' "$OUT/smoke-stdout.txt"; then
  ok "stdout is transcript"
else
  bad "stdout missing transcript"
fi

# --- 3) text backend → worker wrap ---
log "text backend → worker prompt"
WORKER_TXT="Implement the DoD in monitor-brief and run make eval-structural"
if ! "$PY" "$EDGE/stt_edge.py" --backend text --text "$WORKER_TXT" --target worker --out-dir "$OUT" >/dev/null; then
  bad "text→worker failed"
else
  if grep -q 'OpenCode \*\*worker\*\*' "$OUT/agent-prompt.md" || grep -qi 'worker' "$OUT/agent-prompt.md"; then
    ok "worker-targeted prompt"
  else
    bad "worker prompt not wrapped"
  fi
  if grep -F "$WORKER_TXT" "$OUT/last-transcript.txt" >/dev/null; then
    ok "worker transcript exact"
  else
    bad "worker transcript mismatch"
  fi
fi

# --- 4) raw target ---
log "raw target"
if ! "$PY" "$EDGE/stt_edge.py" --backend text --text "ping" --target raw --out-dir "$OUT" >/dev/null; then
  bad "raw target failed"
else
  if [[ "$(cat "$OUT/agent-prompt.md")" == "ping" ]] || grep -qx 'ping' "$OUT/agent-prompt.md"; then
    ok "raw prompt is transcript only"
  else
    # allow trailing newline only
    if [[ "$(tr -d '\n' <"$OUT/agent-prompt.md")" == "ping" ]]; then
      ok "raw prompt is transcript only"
    else
      bad "raw prompt has wrapper: $(head -c 80 "$OUT/agent-prompt.md")"
    fi
  fi
fi

# --- 5) optional real STT probe (informational) ---
log "optional STT backend probe"
STT_NOTE="none"
if "$PY" -c "import whisper" 2>/dev/null; then
  STT_NOTE="openai-whisper importable"
  ok "local whisper available (not exercised without audio fixture)"
elif "$PY" -c "import faster_whisper" 2>/dev/null; then
  STT_NOTE="faster-whisper importable"
  ok "faster-whisper available (not exercised without audio fixture)"
elif [[ -n "${OPENAI_API_KEY:-}" ]]; then
  STT_NOTE="OPENAI_API_KEY set (cloud Whisper ready)"
  ok "cloud Whisper key present (not called in smoke)"
else
  STT_NOTE="no local/cloud Whisper — mock/text only (expected for phase-1 lab)"
  ok "no Whisper required for phase-1 smoke"
fi

# --- result receipt ---
STATUS=PASS
[[ "$FAIL" -eq 0 ]] || STATUS=FAIL
{
  echo "# voice-stt-edge smoke"
  echo ""
  echo "- **When:** $(date -Iseconds 2>/dev/null || date)"
  echo "- **Status:** $STATUS"
  echo "- **Out:** \`$OUT\`"
  echo "- **STT probe:** $STT_NOTE"
  echo "- **Phase:** T-0091 p1"
} >"$RESULT_MD"
echo "==> wrote $RESULT_MD"

if [[ "$FAIL" -ne 0 ]]; then
  echo "voice-stt-edge smoke: FAIL" >&2
  exit 1
fi
echo "voice-stt-edge smoke: PASS"
echo ""
echo "Operator (host, with mic + Whisper later):"
echo "  python3 examples/voice-stt-edge/stt_edge.py --mic --seconds 5 --target monitor"
echo "  examples/voice-stt-edge/.generated/handoff.sh"
echo "  # or: grok \"\$(cat examples/voice-stt-edge/.generated/last-transcript.txt)\""
exit 0
