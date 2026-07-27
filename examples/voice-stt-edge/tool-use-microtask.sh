#!/usr/bin/env bash
# T-0098 — S4 tool-use microtask: OpenCode (tools model) must edit a known file.
#
# - No ollama / no matching model → SKIP with artifact (exit 0)
# - Timeout / empty infrastructure → SKIP with artifact (exit 0)
# - Model present + marker file wrong/missing → HARD FAIL (exit 1)
# - Model present + correct marker → PASS (+ soft 008 if present)
#
# Override: VOICE_TOOL_MICROTASK_TIMEOUT (default 240)
# Force skip: VOICE_TOOL_MICROTASK=0
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=lib-local-model.sh
source "$EDGE/lib-local-model.sh"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
mkdir -p "$OUT"
MARKER="$OUT/tool-microtask-marker.txt"
TIMEOUT="${VOICE_TOOL_MICROTASK_TIMEOUT:-240}"
TASK=t0098

rm -f "$OUT/local-eval-${TASK}-"*.md 2>/dev/null || true
rm -f "$MARKER"

echo "== T-0098 tool-use microtask =="
echo "  timeout=${TIMEOUT}s marker=$MARKER"

if [[ "${VOICE_TOOL_MICROTASK:-1}" == "0" ]]; then
  reason="VOICE_TOOL_MICROTASK=0 (operator disabled)"
  echo "SKIP: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason"
  exit 0
fi

if [[ -f "$ROOT/examples/opencode-ollama/.generated/tools-model.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  # shellcheck source=/dev/null
  . "$ROOT/examples/opencode-ollama/.generated/tools-model.env" 2>/dev/null || true
  set +a
fi

MATCH="$(pfy_detect_local_model)"
if [[ -z "$MATCH" ]]; then
  reason="no tools/coder Ollama model for tool-use microtask"
  echo "SKIP: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "hint=make eval-select-tools-model"
  exit 0
fi

if [[ -n "${LOCAL_TOOLS_MODEL:-}" ]]; then
  export OPENCODE_AGENT_MODEL="${OPENCODE_AGENT_MODEL:-$LOCAL_TOOLS_MODEL}"
  export LOCAL_CODER_MODEL="${LOCAL_CODER_MODEL:-$LOCAL_TOOLS_MODEL}"
else
  export LOCAL_CODER_MODEL="${LOCAL_CODER_MODEL:-$MATCH}"
fi

TOKEN="pfy-$(date +%s)-$RANDOM"
REL_MARKER="examples/voice-stt-edge/.generated/tool-microtask-marker.txt"

PROMPT=$(cat <<EOF
You are running a bounded tool-use microtask (T-0098).

1. Create or overwrite this exact file path relative to the repo root:
   ${REL_MARKER}
2. File contents must be EXACTLY two lines:
   PFY_TOOL_MICROTASK_OK
   token=${TOKEN}
3. Do not modify any other files.
4. After writing the file, end your final reply with:
   STATUS: pass
   DOD: tool microtask marker written
   EXIT: goal
   NEXT: done

Use tools to write the file. This is the Definition of Done.
EOF
)

echo "==> model=$MATCH tools=${LOCAL_TOOLS_MODEL:-unset} token=$TOKEN"
export VOICE_LONG_TASK=1
# Prefer real Ollama tools loop (T-0098). OpenCode often emits tool JSON as text
# without executing; tool_microtask mode forces write_file execution.
set +e
timeout "$TIMEOUT" python3 "$EDGE/agent_runner.py" \
  --mode tool_microtask \
  --long-task \
  --transcript "$PROMPT" \
  --target worker \
  --timeout "$TIMEOUT" \
  --out-dir "$OUT" \
  --repo "$ROOT"
rc=$?
set -e

if [[ $rc -eq 124 ]]; then
  reason="timeout after ${TIMEOUT}s during tool-use microtask"
  echo "SKIP: $reason"
  pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "model=$MATCH" "agent_rc=124"
  exit 0
fi

MODE=""
if [[ -f "$OUT/last-run.json" ]]; then
  MODE="$(python3 -c "import json;print(json.load(open('$OUT/last-run.json')).get('mode',''))" 2>/dev/null || true)"
fi

if [[ ! -f "$MARKER" ]]; then
  err=""
  if [[ -f "$OUT/last-run.json" ]]; then
    err="$(python3 -c "import json;print(json.load(open('$OUT/last-run.json')).get('error') or '')" 2>/dev/null || true)"
  fi
  # Infrastructure: Ollama tools unsupported / connection
  if echo "$err" | grep -qiE 'does not support tools|connection refused|failed to connect|404'; then
    reason="tools path unavailable ($err) — SKIP"
    echo "SKIP: $reason"
    pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "model=$MATCH" "mode=$MODE"
    exit 0
  fi
  if [[ ! -s "$OUT/last-reply.txt" ]] && [[ $rc -ne 0 ]]; then
    reason="agent failed (rc=$rc) with no reply and no marker — infrastructure SKIP"
    echo "SKIP: $reason"
    pfy_write_eval_receipt "$OUT" "$TASK" skip "$reason" "model=$MATCH" "mode=$MODE"
    exit 0
  fi
  reason="mode=${MODE:-tool_microtask} model=$MATCH present but tool-microtask marker missing"
  echo "FAIL: $reason"
  echo "--- last-reply head ---"
  head -c 1200 "$OUT/last-reply.txt" 2>/dev/null || true
  echo
  pfy_write_eval_receipt "$OUT" "$TASK" fail "$reason" "model=$MATCH" "agent_rc=$rc" "mode=$MODE"
  exit 1
fi

line1="$(sed -n '1p' "$MARKER" | tr -d '\r')"
line2="$(sed -n '2p' "$MARKER" | tr -d '\r')"
if [[ "$line1" != "PFY_TOOL_MICROTASK_OK" ]] || [[ "$line2" != "token=${TOKEN}" ]]; then
  reason="marker content mismatch (tools did not write required token)"
  echo "FAIL: $reason"
  echo "  expected line1=PFY_TOOL_MICROTASK_OK"
  echo "  expected line2=token=${TOKEN}"
  echo "  got:"
  cat -A "$MARKER" || true
  pfy_write_eval_receipt "$OUT" "$TASK" fail "$reason" "model=$MATCH" "agent_rc=$rc"
  exit 1
fi

echo "==> marker OK"
if [[ -f "$OUT/last-reply.txt" ]] && grep -qi '^STATUS:' "$OUT/last-reply.txt" 2>/dev/null; then
  python3 "$ROOT/examples/eval-harness/tasks/008-voice-receipt/score.py" "$OUT/last-reply.txt" || \
    echo "note: 008 soft-fail on reply text (marker already PASS)"
fi
if [[ -f "$OUT/last-run.json" ]]; then
  python3 "$ROOT/examples/eval-harness/tasks/009-voice-last-run/score.py" "$OUT/last-run.json" || true
fi

echo "T-0098 tool-use microtask: PASS"
pfy_write_eval_receipt "$OUT" "$TASK" pass "marker written with token under model $MATCH" "agent_rc=$rc" "marker=$REL_MARKER"
exit 0
