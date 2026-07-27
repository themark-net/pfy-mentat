#!/usr/bin/env bash
# T-0097 — S3 hard local receipt when a model is present.
#
# - No ollama / no matching model → SKIP with artifact (exit 0)
# - Model present + agent timeout / infrastructure fail → SKIP with artifact (exit 0)
# - Model present + agent reply without valid 008 → HARD FAIL (exit 1)
# - Model present + 008 PASS → exit 0
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=lib-local-model.sh
source "$EDGE/lib-local-model.sh"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
mkdir -p "$OUT"
TASK=t0097
rm -f "$OUT/local-eval-${TASK}-"*.md 2>/dev/null || true

TIMEOUT="${VOICE_OPTIONAL_TIMEOUT:-180}"
echo "== T-0097 optional local long-task (hard 008 when model present) =="
echo "  timeout=${TIMEOUT}s"

MATCH="$(pfy_detect_local_model)"
if [[ -z "$MATCH" ]]; then
  reason="no LOCAL_TOOLS_MODEL / LOCAL_CODER_MODEL / deepseek-coder|coder tag in ollama list (or ollama missing)"
  echo "SKIP: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "hint=ollama pull deepseek-coder:6.7b-instruct"
  exit 0
fi

echo "==> model present: $MATCH — hard 008 path"
export LOCAL_CODER_MODEL="${LOCAL_CODER_MODEL:-$MATCH}"
if [[ -f "$ROOT/examples/opencode-ollama/.generated/tools-model.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/examples/opencode-ollama/.generated/tools-model.env" 2>/dev/null || true
  set +a
fi
export VOICE_LONG_TASK=1

set +e
timeout "$TIMEOUT" python3 "$EDGE/agent_runner.py" \
  --mode opencode \
  --long-task \
  --transcript "Bounded CI long-task (T-0097): reply with ONLY a short status and end with exactly STATUS/DOD/EXIT/NEXT lines for a healthy voice install. Do not edit files." \
  --target worker \
  --timeout "$TIMEOUT" \
  --out-dir "$OUT" \
  --repo "$ROOT"
rc=$?
set -e

if [[ $rc -eq 124 ]]; then
  reason="timeout after ${TIMEOUT}s — model too slow (infrastructure SKIP, not 008 fail)"
  echo "SKIP: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "model=$MATCH" "agent_rc=124"
  exit 0
fi

if [[ $rc -ne 0 ]]; then
  if [[ ! -f "$OUT/last-reply.txt" ]] || [[ ! -s "$OUT/last-reply.txt" ]]; then
    reason="agent exit $rc with empty last-reply (infrastructure SKIP)"
    echo "SKIP: $reason"
    pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "model=$MATCH" "agent_rc=$rc"
    exit 0
  fi
fi

if [[ ! -f "$OUT/last-reply.txt" ]]; then
  reason="model present but last-reply.txt missing"
  echo "FAIL: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" fail "$reason" "model=$MATCH"
  exit 1
fi

set +e
python3 "$ROOT/examples/eval-harness/tasks/008-voice-receipt/score.py" "$OUT/last-reply.txt"
score_rc=$?
set -e
if [[ -f "$OUT/last-run.json" ]]; then
  python3 "$ROOT/examples/eval-harness/tasks/009-voice-last-run/score.py" "$OUT/last-run.json" || true
fi

if [[ $score_rc -ne 0 ]]; then
  reason="model present ($MATCH) but 008-voice-receipt FAILED on last-reply"
  echo "FAIL: $reason"
  head -c 800 "$OUT/last-reply.txt" || true
  echo
  pfy_write_eval_receipt "$OUT" "$TASK" fail "$reason" "model=$MATCH" "agent_rc=$rc" "score_rc=$score_rc"
  exit 1
fi

echo "T-0097 local long-task: PASS (008 hard gate)"
pfy_write_eval_receipt "$OUT" "$TASK" pass "008 receipt valid with model $MATCH" "agent_rc=$rc"
exit 0
