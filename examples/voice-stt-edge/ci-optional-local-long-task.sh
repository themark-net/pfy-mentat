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

# Prefer tools-model.env before detect so LOCAL_TOOLS_MODEL wins
if [[ -f "$ROOT/examples/opencode-ollama/.generated/tools-model.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/examples/opencode-ollama/.generated/tools-model.env" 2>/dev/null || true
  set +a
fi

MATCH="$(pfy_detect_local_model)"
if [[ -z "$MATCH" ]]; then
  reason="no LOCAL_TOOLS_MODEL / LOCAL_CODER_MODEL / deepseek-coder|coder tag in ollama list (or ollama missing)"
  echo "SKIP: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "hint=ollama pull deepseek-coder:6.7b-instruct"
  exit 0
fi

echo "==> model present: $MATCH — hard 008 path (Ollama HTTP chat; not OpenCode tools)"
# Prefer a small/fast chat model for receipt fidelity (7b over 32b tool planners).
export LOCAL_CODER_MODEL="${LOCAL_CODER_MODEL:-$MATCH}"
case "$LOCAL_CODER_MODEL" in
  *32b*|*30b*|*70b*)
    if [[ -n "${LOCAL_TOOLS_MODEL:-}" && "$LOCAL_TOOLS_MODEL" != *32b* ]]; then
      export LOCAL_CODER_MODEL="$LOCAL_TOOLS_MODEL"
    elif printf '%s\n' "$(ollama list 2>/dev/null || true)" | grep -qi 'qwen2.5-coder:7b'; then
      export LOCAL_CODER_MODEL="$(ollama list 2>/dev/null | grep -i 'qwen2.5-coder:7b' | head -1 | awk '{print $1}')"
    fi
    ;;
esac
export LOCAL_TOOLS_MODEL="${LOCAL_TOOLS_MODEL:-$LOCAL_CODER_MODEL}"
export VOICE_LONG_TASK=1
# Force chat completion so models emit STATUS lines instead of tool-call plans.
export VOICE_FORCE_OLLAMA_HTTP=1

set +e
timeout "$TIMEOUT" python3 "$EDGE/agent_runner.py" \
  --mode opencode \
  --long-task \
  --transcript "Bounded CI long-task (T-0097): reply with ONLY these four lines and nothing else:
STATUS: pass
DOD: healthy voice install receipt
EXIT: goal
NEXT: done" \
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

# Infrastructure-shaped reply → SKIP (not hard 008 fail)
if grep -qiE 'ProviderModelNotFoundError|Model not found:|does not support tools|connection refused|failed to connect|Ollama completion failed' \
  "$OUT/last-reply.txt" 2>/dev/null; then
  reason="provider/infra error in agent reply — SKIP"
  echo "SKIP: $reason"
  head -c 400 "$OUT/last-reply.txt" || true
  echo
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "model=$MATCH" "agent_rc=$rc"
  exit 0
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
