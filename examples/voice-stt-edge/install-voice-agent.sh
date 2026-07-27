#!/usr/bin/env bash
# Installable voice interactive agent path (local-first, cloud escalate).
# Does not require mic. Proves wiring + agent + structural rubric gates.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
EDGE="$ROOT/examples/voice-stt-edge"

echo "== pfy-mentat voice-agent install (local-first) =="
echo "  root=$ROOT"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required tool: $1" >&2
    exit 2
  fi
  echo "  OK  $1"
}

need python3
need make
need curl

chmod +x \
  "$EDGE/smoke.sh" "$EDGE/smoke-agent.sh" "$EDGE/smoke-remote.sh" \
  "$EDGE/agent_runner.py" "$EDGE/stt_edge.py" "$EDGE/remote_server.py" \
  "$EDGE/python.sh" "$EDGE/install-local-stt.sh" "$EDGE/listen.sh" \
  "$EDGE/install-voice-agent.sh" 2>/dev/null || true

echo "==> structural rubric (no LLM)"
make eval-structural

echo "==> voice STT wiring"
make smoke-voice-stt

echo "==> voice agent (mock + local + remote hook)"
make smoke-voice-agent

echo "==> long-task mock + 008 receipt"
export VOICE_LONG_TASK=1
python3 "$EDGE/agent_runner.py" \
  --mode mock \
  --long-task \
  --transcript "Install path long-task: prove STATUS/DOD/EXIT/NEXT receipt" \
  --target worker \
  --out-dir "$EDGE/.generated" \
  --repo "$ROOT"
python3 "$ROOT/examples/eval-harness/tasks/008-voice-receipt/score.py" \
  "$EDGE/.generated/last-reply.txt"

echo ""
echo "voice-agent install: PASS (wiring + rubric)"
echo ""
echo "Daily operator path:"
echo "  # local bulk (default)"
echo "  VOICE_AUTO_AGENT=opencode VOICE_LONG_TASK=1 make voice-agent-run"
echo "  # or text without mic:"
echo "  python3 examples/voice-stt-edge/stt_edge.py --text 'your task' --target worker"
echo "  VOICE_LONG_TASK=1 make voice-agent-run"
echo "  # cloud escalate"
echo "  VOICE_AUTO_AGENT=grok make voice-agent-run"
echo "  # desk mic (optional)"
echo "  make voice-stt-install && make voice-listen"
echo "  # remote phone"
echo "  export VOICE_REMOTE_TOKEN=...; make voice-remote"
exit 0
