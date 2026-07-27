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
  "$EDGE/install-voice-agent.sh" "$EDGE/voice-repl.sh" \
  "$EDGE/e2e-develop-loop.sh" "$EDGE/ci-optional-local-long-task.sh" 2>/dev/null || true

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

echo "==> deterministic e2e develop-loop (recipe)"
"$EDGE/e2e-develop-loop.sh"

echo ""
echo "voice-agent install: PASS (wiring + rubric + e2e)"
echo ""
echo "Daily operator path (see docs/ops/voice-agent-install.md):"
echo "  make voice-repl                          # text REPL, long-task receipts"
echo "  VOICE_TEXT='your task' make voice-agent-run"
echo "  VOICE_AUTO_AGENT=grok make voice-agent-run   # cloud escalate"
echo "  make voice-agent-long-mock               # mock + 008"
echo "  make voice-stt-install && make voice-listen  # desk mic (optional)"
echo "  export VOICE_REMOTE_TOKEN=...; make voice-remote"
exit 0
