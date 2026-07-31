#!/usr/bin/env bash
# Deterministic end-to-end develop loop (no LLM required).
# text task → agent_runner (recipe) → file change → make eval-structural green.
#
# Optional real local path when models present:
#   VOICE_E2E_TRY_OPENCODE=1 ./examples/voice-stt-edge/e2e-develop-loop.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
mkdir -p "$OUT"

echo "== voice e2e develop-loop =="
echo "  root=$ROOT out=$OUT"

# 1) Always prove deterministic multi-step path through agent_runner
export VOICE_LONG_TASK=1
python3 "$EDGE/agent_runner.py" \
  --mode recipe \
  --long-task \
  --transcript "PFY e2e: write marker fixture and re-run make eval-structural" \
  --target worker \
  --timeout 180 \
  --out-dir "$OUT" \
  --repo "$ROOT"

MARKER="$OUT/e2e-loop-marker.txt"
test -f "$MARKER" || { echo "FAIL: marker missing at $MARKER" >&2; exit 1; }
python3 "$ROOT/examples/eval-harness/tasks/008-voice-receipt/score.py" "$OUT/last-reply.txt"
python3 "$ROOT/examples/eval-harness/tasks/009-voice-last-run/score.py" "$OUT/last-run.json"
make eval-structural

echo "==> deterministic recipe path: PASS (marker + 008 + 009 + structural)"

# 2) Soft-optional: real OpenCode/Ollama long-task when model is present
if [[ "${VOICE_E2E_TRY_OPENCODE:-0}" == "1" ]] || [[ "${VOICE_E2E_TRY_OPENCODE:-}" == "auto" ]]; then
  if command -v ollama >/dev/null 2>&1; then
    MODEL="${LOCAL_TOOLS_MODEL:-${LOCAL_CODER_MODEL:-deepseek-coder:6.7b}}"
    if ollama list 2>/dev/null | grep -qiE 'deepseek-coder|'"$(printf '%s' "$MODEL" | sed 's/:/.*/')" ; then
      echo "==> optional real local long-task (model present)…"
      set +e
      timeout "${VOICE_AGENT_TIMEOUT:-180}" python3 "$EDGE/agent_runner.py" \
        --mode opencode \
        --long-task \
        --transcript "Reply only with STATUS/DOD/EXIT/NEXT for a healthy voice e2e; do not edit files." \
        --target worker \
        --timeout "${VOICE_AGENT_TIMEOUT:-180}" \
        --out-dir "$OUT" \
        --repo "$ROOT"
      oc_rc=$?
      set -e
      if [[ $oc_rc -eq 0 ]]; then
        echo "==> optional opencode long-task: ran (exit 0)"
      else
        echo "==> optional opencode long-task: soft-skip (exit $oc_rc; not a hard fail)"
      fi
    else
      echo "==> optional opencode: SKIP (no deepseek-coder / LOCAL_* model in ollama list)"
    fi
  else
    echo "==> optional opencode: SKIP (ollama not on PATH)"
  fi
fi

echo ""
echo "voice e2e develop-loop: PASS"
exit 0
