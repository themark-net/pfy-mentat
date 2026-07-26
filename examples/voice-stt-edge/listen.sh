#!/usr/bin/env bash
# Real mic → STT → agent handoff artifacts (T-0091). Not the smoke.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"
# shellcheck source=python.sh
source "$EDGE/python.sh"
OUT="${VOICE_STT_OUT:-$EDGE/.generated}"
LISTEN_SECS="${VOICE_LISTEN_SECONDS:-5}"
TARGET="${VOICE_TARGET:-monitor}"
BACKEND="${VOICE_STT_BACKEND:-auto}"
HANDOFF="${VOICE_HANDOFF:-0}"

echo "== voice-listen (real STT; not smoke) =="
echo "  python=$VOICE_PY"
echo "  seconds=$LISTEN_SECS target=$TARGET backend=$BACKEND"
echo "  NOTE: make smoke-voice-stt only tests mock/text wiring — no mic."

if [[ ! -x "$EDGE/.venv/bin/python" ]] && ! "$VOICE_PY" -c "import faster_whisper" 2>/dev/null; then
  echo "" >&2
  echo "error: no STT venv / faster-whisper. Install first (PEP 668-safe):" >&2
  echo "  make voice-stt-install" >&2
  exit 2
fi

if ! "$VOICE_PY" "$EDGE/stt_edge.py" --probe; then
  echo "" >&2
  echo "error: no STT backend ready. Install first:" >&2
  echo "  make voice-stt-install" >&2
  exit 2
fi

ARGS=(--mic --seconds "$LISTEN_SECS" --target "$TARGET" --backend "$BACKEND" --out-dir "$OUT")
if [[ "$HANDOFF" == "1" ]]; then
  ARGS+=(--handoff)
fi

"$VOICE_PY" "$EDGE/stt_edge.py" "${ARGS[@]}"
echo ""
echo "If transcript looks right:"
echo "  $OUT/handoff.sh"
echo "  # or: grok \"\$(cat $OUT/agent-prompt.md)\""
