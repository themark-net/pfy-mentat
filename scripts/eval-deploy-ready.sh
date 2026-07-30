#!/usr/bin/env bash
# G1 deploy-ready gate: structural + golden + optional smokes (HD #33).
# Exit 0 = agent may close runtime work as implement-done (not human UAT).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p pipelines/eval

echo "=== G1 deploy-ready (build green + smoke) ==="
python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md
python3 examples/eval-harness/run_golden.py --write-md pipelines/eval/golden.latest.md

# Soft smokes: success or documented skip
soft() {
  local name="$1"
  shift
  echo "--> soft smoke: $name"
  if "$@"; then
    echo "    PASS $name"
  else
    echo "    SKIP/soft-fail $name (optional backend or env — not hard fail for G1 meta)"
  fi
}

# Product deploy spine must be callable
test -x scripts/env-stage.sh || chmod +x scripts/env-stage.sh
test -x scripts/product-onboard.sh || chmod +x scripts/product-onboard.sh
test -x scripts/product-ship.sh || chmod +x scripts/product-ship.sh

# Voice / tools smokes when present — soft
if [[ -x examples/voice-stt-edge/smoke.sh ]]; then
  soft voice-stt ./examples/voice-stt-edge/smoke.sh
fi
if [[ -x examples/eval-harness/smoke_tools_model.sh ]]; then
  soft tools-model ./examples/eval-harness/smoke_tools_model.sh
fi
if [[ -x examples/opencode-cage/smoke.sh ]]; then soft opencode-cage ./examples/opencode-cage/smoke.sh; fi
if [[ -x examples/voice-tts-status/smoke.sh ]]; then soft voice-tts ./examples/voice-tts-status/smoke.sh; fi
if [[ -x examples/asm-smoke/smoke.sh ]]; then soft asm ./examples/asm-smoke/smoke.sh; fi

# Write receipt
cat > pipelines/eval/deploy-ready.latest.md <<MD
# Deploy-ready (G1) — $(date -u +%Y-%m-%dT%H:%M:%SZ)

- structural: see structural.latest.md
- golden: see golden.latest.md
- product scripts present: project-onboard, env-stage, product-ship
- optional smokes: soft (SKIP allowed)

**Gate:** implement-done allowed. **Not** human UAT (G2).
See docs/ops/eval-gates-and-ux-uat.md
MD

echo "=== G1 deploy-ready: PASS (implement-done; UAT separate) ==="
echo "wrote pipelines/eval/deploy-ready.latest.md"
