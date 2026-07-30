#!/usr/bin/env bash
# T-0074 eval-auto: structural always; implement ladder if Ollama up.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p pipelines/eval

python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md

if ! curl -sf --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  if [[ "${EVAL_AUTO_REQUIRE_OLLAMA:-0}" == "1" ]]; then
    echo "eval-auto: Ollama required but unreachable" >&2
    exit 1
  fi
  cat > pipelines/eval/eval-auto.latest.md <<MD
# eval-auto soft-skip $(date -u +%Y-%m-%dT%H:%M:%SZ)
status: soft-skip
reason: Ollama not on :11434
note: structural green; set EVAL_AUTO_REQUIRE_OLLAMA=1 to hard-fail
MD
  echo "eval-auto: SOFT-SKIP (Ollama not on :11434) — structural already green"
  exit 0
fi

./examples/litellm-ollama/host-ollama-gateway.sh start 2>/dev/null || true
python3 examples/eval-harness/select_ollama_models.py --pull-gate
python3 examples/eval-harness/select_ollama_models.py --exports 2>/dev/null \
  | grep -E '^(EVAL_|LITELLM_)' > /tmp/pfy-eval-model-exports.sh
echo "==> using selected models:"; cat /tmp/pfy-eval-model-exports.sh
set -a
# shellcheck disable=SC1091
source /tmp/pfy-eval-model-exports.sh
set +a
cands="${EVAL_GATE_CANDIDATES:-${EVAL_GATE_MODEL:-}}"
ok=0
IFS=',' read -ra arr <<<"$cands"
for g in "${arr[@]}"; do
  g="$(echo "$g" | tr -d ' ')"
  [[ -z "$g" ]] && continue
  echo "==> eval-v02 gate candidate: $g"
  if make eval-v02 \
    EVAL_MODEL="$g" EVAL_GATE_MODEL="$g" \
    EVAL_MODELS="${EVAL_MODELS:-}" \
    LITELLM_SMOKE_MODEL="${LITELLM_SMOKE_MODEL:-deepseek-coder:latest}"; then
    ok=1
    echo "eval-auto: PASS with gate $g"
    echo "status: pass gate=$g" > pipelines/eval/eval-auto.latest.md
    break
  fi
  echo "eval-auto: gate $g failed — try next candidate"
done
[[ $ok -eq 1 ]] || { echo "eval-auto: all gate candidates failed"; exit 1; }
