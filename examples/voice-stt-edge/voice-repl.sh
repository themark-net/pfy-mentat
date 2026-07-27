#!/usr/bin/env bash
# Interactive voice-agent REPL (text). No mic required.
# Local OpenCode/Ollama by default; VOICE_AUTO_AGENT=grok to escalate.
#
#   ./examples/voice-stt-edge/voice-repl.sh
#   VOICE_LONG_TASK=1 VOICE_AUTO_AGENT=opencode ./examples/voice-stt-edge/voice-repl.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=python.sh
source "$EDGE/python.sh"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
mkdir -p "$OUT"

export VOICE_LONG_TASK="${VOICE_LONG_TASK:-1}"
MODE="${VOICE_AUTO_AGENT:-${VOICE_AGENT_MODE:-opencode}}"
TARGET="${VOICE_TARGET:-worker}"
TIMEOUT="${VOICE_AGENT_TIMEOUT:-600}"

echo "== pfy voice-agent REPL =="
echo "  mode=$MODE target=$TARGET long_task=$VOICE_LONG_TASK"
echo "  repo=$ROOT"
echo "  commands: /status /mode <opencode|grok|mock> /target <worker|monitor> /quit"
echo ""

while true; do
  printf 'voice> '
  if ! IFS= read -r line; then
    echo
    break
  fi
  case "$line" in
    "") continue ;;
    /quit|/exit|quit|exit)
      echo "bye"
      break
      ;;
    /status)
      "$VOICE_PY" "$EDGE/agent_runner.py" --status --out-dir "$OUT"
      continue
      ;;
    /mode\ *)
      MODE="${line#/mode }"
      export VOICE_AUTO_AGENT="$MODE"
      echo "  mode=$MODE"
      continue
      ;;
    /target\ *)
      TARGET="${line#/target }"
      echo "  target=$TARGET"
      continue
      ;;
    /*)
      echo "  unknown command: $line"
      continue
      ;;
  esac

  echo "==> running agent…"
  set +e
  "$VOICE_PY" "$EDGE/agent_runner.py" \
    --mode "$MODE" \
    --long-task \
    --transcript "$line" \
    --target "$TARGET" \
    --timeout "$TIMEOUT" \
    --out-dir "$OUT" \
    --repo "$ROOT"
  RC=$?
  set -e
  echo "==> exit=$RC"
  if [[ -f "$OUT/last-reply.txt" ]]; then
    echo "--- reply ---"
    head -c 4000 "$OUT/last-reply.txt"
    echo
    echo "-------------"
    if grep -qi '^STATUS:' "$OUT/last-reply.txt" 2>/dev/null; then
      "$VOICE_PY" "$ROOT/examples/eval-harness/tasks/008-voice-receipt/score.py" \
        "$OUT/last-reply.txt" || true
    fi
  fi
done
