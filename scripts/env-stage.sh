#!/usr/bin/env bash
# Product lever 2: stage — structural eval + optional local OpenAI-compat path green.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> env-stage (product local path)"
python3 bootstrap/env/check_env.py || {
  echo "env-check failed — run make env-init and edit .env (DEPLOY_PROFILE)"
  exit 1
}
python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md
# Soft local path: detector (ADR-0014) then Ollama adapter fallback
RT_JSON=""
if [[ -f scripts/detect-local-runtime.sh ]]; then
  RT_JSON=$(bash scripts/detect-local-runtime.sh --json 2>/dev/null || true)
  echo "local runtime: ${RT_JSON:-unknown}"
fi
if curl -sf --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama adapter up — running smoke-litellm-ollama if cage available"
  make smoke-litellm-ollama 2>/dev/null || echo "smoke-litellm soft-skip (cage/host path not ready)"
elif curl -sf --max-time 2 http://127.0.0.1:8080/v1/models >/dev/null 2>&1 \
  || curl -sf --max-time 2 http://127.0.0.1:11435/v1/models >/dev/null 2>&1; then
  echo "local OpenAI-compat up (llama-swap/llama-server/Shimmy) — structural only this track"
else
  echo "no local runtime on :11434/:8080/:11435 — structural only (local bulk SKIP; still stage OK for docs track)"
fi
echo "env-stage: green for structural; local LLM optional"
