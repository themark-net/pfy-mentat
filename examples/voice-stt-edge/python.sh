#!/usr/bin/env bash
# Resolve Python for voice-stt-edge: prefer local .venv (PEP 668 safe).
# Usage: source this file, then use "$VOICE_PY"
#   or:  examples/voice-stt-edge/python.sh -c 'import faster_whisper'
set -euo pipefail
EDGE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$EDGE/.venv/bin/python"

if [[ -n "${VOICE_STT_PYTHON:-}" && -x "${VOICE_STT_PYTHON}" ]]; then
  VOICE_PY="$VOICE_STT_PYTHON"
elif [[ -x "$VENV_PY" ]]; then
  VOICE_PY="$VENV_PY"
elif [[ -n "${PYTHON:-}" && -x "${PYTHON}" ]]; then
  VOICE_PY="$PYTHON"
else
  VOICE_PY="$(command -v python3)"
fi

export VOICE_PY
export VOICE_STT_VENV="$EDGE/.venv"

# If executed (not sourced), run python with remaining args
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  exec "$VOICE_PY" "$@"
fi
