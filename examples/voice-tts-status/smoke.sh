#!/usr/bin/env bash
# T-0094 — optional short local TTS status (not duplex). Soft by default.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
mkdir -p pipelines/smoke/voice-tts
OUT=pipelines/smoke/voice-tts/results.latest.md
echo "# Voice TTS status smoke" >"$OUT"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$OUT"
echo "policy: short status only; not duplex (ADR-0012)" >>"$OUT"
# Detect common local TTS binaries without installing
found=0
for b in piper say espeak-ng espeak; do
  if command -v "$b" >/dev/null 2>&1; then
    echo "found: $b" >>"$OUT"
    found=1
  fi
done
if [[ $found -eq 0 ]]; then
  echo "status: soft-skip (no local TTS binary; optional install piper/kokoro later)" | tee -a "$OUT"
  echo "voice-tts: SOFT-SKIP (status probe only)"
  exit 0
fi
echo "status: probe-ok (binary present; full synthesis not required for G1)" | tee -a "$OUT"
echo "voice-tts: PASS (probe)"
exit 0
