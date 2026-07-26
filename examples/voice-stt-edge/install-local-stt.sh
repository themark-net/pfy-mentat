#!/usr/bin/env bash
# Install local Whisper STT for T-0091 real mic path (host).
# Smoke (make smoke-voice-stt) does NOT need this — it is mock/text only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

echo "== voice-stt-install (faster-whisper) =="
echo "  This downloads Python packages (+ first-run model weights on next listen)."
echo "  Prefer a user install to avoid system site-packages fights."

if ! "$PY" -m pip --version >/dev/null 2>&1; then
  echo "error: $PY -m pip not available" >&2
  exit 1
fi

# faster-whisper is lighter than openai-whisper+torch full stack for many hosts
"$PY" -m pip install --user -U 'faster-whisper>=1.0.0'

echo "==> verifying import"
"$PY" -c "from faster_whisper import WhisperModel; print('  faster_whisper: OK')"

echo "==> probe"
"$PY" examples/voice-stt-edge/stt_edge.py --probe || true

echo ""
echo "Next (host with mic):"
echo "  make voice-listen"
echo "  # or re-transcribe an existing capture:"
echo "  python3 examples/voice-stt-edge/stt_edge.py \\"
echo "    --audio examples/voice-stt-edge/.generated/last-capture.wav \\"
echo "    --backend local --target monitor"
echo "  examples/voice-stt-edge/.generated/handoff.sh"
