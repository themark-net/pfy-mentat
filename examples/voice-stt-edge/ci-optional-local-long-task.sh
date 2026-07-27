#!/usr/bin/env bash
# Soft-optional real local long-task for CI (voice-clean).
# If ollama lists LOCAL_TOOLS_MODEL or deepseek-coder → run one bounded long-task.
# Else SKIP with reason — never fail CI for missing models.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
mkdir -p "$OUT"

TIMEOUT="${VOICE_OPTIONAL_TIMEOUT:-180}"
MODEL_HINT="${LOCAL_TOOLS_MODEL:-${LOCAL_CODER_MODEL:-deepseek-coder}}"

echo "== optional local long-task =="
echo "  timeout=${TIMEOUT}s model_hint=$MODEL_HINT"

if ! command -v ollama >/dev/null 2>&1; then
  echo "SKIP: ollama not on PATH (no local model path)"
  exit 0
fi

LIST="$(ollama list 2>/dev/null || true)"
if [[ -z "$LIST" ]]; then
  echo "SKIP: ollama list empty / unreachable"
  exit 0
fi

# Match LOCAL_TOOLS_MODEL, LOCAL_CODER_MODEL, or any deepseek-coder tag
MATCH=""
if [[ -n "${LOCAL_TOOLS_MODEL:-}" ]] && printf '%s\n' "$LIST" | grep -qF "${LOCAL_TOOLS_MODEL%%:*}"; then
  MATCH="$LOCAL_TOOLS_MODEL"
elif [[ -n "${LOCAL_CODER_MODEL:-}" ]] && printf '%s\n' "$LIST" | grep -qF "${LOCAL_CODER_MODEL%%:*}"; then
  MATCH="$LOCAL_CODER_MODEL"
elif printf '%s\n' "$LIST" | grep -qi 'deepseek-coder'; then
  MATCH="$(printf '%s\n' "$LIST" | grep -i 'deepseek-coder' | head -1 | awk '{print $1}')"
fi

if [[ -z "$MATCH" ]]; then
  echo "SKIP: no LOCAL_TOOLS_MODEL / deepseek-coder in ollama list"
  echo "  (hint: ollama pull deepseek-coder:6.7b-instruct)"
  exit 0
fi

echo "==> model present: $MATCH — running bounded opencode long-task"
export LOCAL_CODER_MODEL="${LOCAL_CODER_MODEL:-$MATCH}"
export VOICE_LONG_TASK=1
# Soft-fail: model may be slow/broken; never fail the workflow for that alone
set +e
timeout "$TIMEOUT" python3 "$EDGE/agent_runner.py" \
  --mode opencode \
  --long-task \
  --transcript "Bounded CI long-task: reply with STATUS/DOD/EXIT/NEXT for a healthy install; keep it short." \
  --target worker \
  --timeout "$TIMEOUT" \
  --out-dir "$OUT" \
  --repo "$ROOT"
rc=$?
set -e

if [[ $rc -eq 0 ]]; then
  echo "optional local long-task: PASS (agent exit 0)"
  if [[ -f "$OUT/last-reply.txt" ]] && grep -qi '^STATUS:' "$OUT/last-reply.txt" 2>/dev/null; then
    python3 "$ROOT/examples/eval-harness/tasks/008-voice-receipt/score.py" \
      "$OUT/last-reply.txt" || echo "note: 008 score soft-failed on LLM reply (not hard fail)"
  fi
elif [[ $rc -eq 124 ]]; then
  echo "optional local long-task: SKIP (timeout after ${TIMEOUT}s — model too slow)"
else
  echo "optional local long-task: SKIP (agent exit $rc — soft; CI continues)"
fi
exit 0
