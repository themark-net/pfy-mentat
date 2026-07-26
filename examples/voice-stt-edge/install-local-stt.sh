#!/usr/bin/env bash
# Install local Whisper STT into a project venv (PEP 668 / Debian-safe).
# Smoke (make smoke-voice-stt) does NOT need this — it is mock/text only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EDGE="$ROOT/examples/voice-stt-edge"
VENV="$EDGE/.venv"
# Host python used only to create the venv
BOOT_PY="${PYTHON:-python3}"

echo "== voice-stt-install (faster-whisper in .venv) =="
echo "  venv: $VENV"
echo "  PEP 668: never pip-install into system Python"
echo "  First listen also downloads Whisper model weights (~tens of MB)."

if ! command -v "$BOOT_PY" >/dev/null 2>&1 && ! [[ -x "$BOOT_PY" ]]; then
  echo "error: need python3 to create venv (BOOT_PY=$BOOT_PY)" >&2
  exit 1
fi

# Ensure venv module exists (Debian: python3-venv / python3-full)
if ! "$BOOT_PY" -c "import venv" 2>/dev/null; then
  echo "error: $BOOT_PY cannot import venv" >&2
  echo "  Debian/Ubuntu: sudo apt install python3-venv python3-full" >&2
  exit 1
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "==> creating venv"
  "$BOOT_PY" -m venv "$VENV"
else
  echo "==> reusing existing venv"
fi

PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

echo "==> upgrading pip"
"$PY" -m pip install -U pip setuptools wheel

echo "==> installing faster-whisper"
"$PIP" install -U 'faster-whisper>=1.0.0'

echo "==> verifying import"
"$PY" -c "from faster_whisper import WhisperModel; print('  faster_whisper: OK')"

# Convenience marker for operators / scripts
echo "$PY" >"$EDGE/.venv-python-path"
echo "==> wrote $EDGE/.venv-python-path"

echo "==> probe (via venv python)"
"$PY" "$EDGE/stt_edge.py" --probe || true

echo ""
echo "Next (host with mic):"
echo "  make voice-listen"
echo "  # or re-transcribe an existing capture:"
echo "  examples/voice-stt-edge/python.sh examples/voice-stt-edge/stt_edge.py \\"
echo "    --audio examples/voice-stt-edge/.generated/last-capture.wav \\"
echo "    --backend local --target monitor"
echo "  examples/voice-stt-edge/.generated/handoff.sh"
