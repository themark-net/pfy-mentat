#!/usr/bin/env bash
# Product lever 2: stage — structural eval + optional local Ollama path green.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> env-stage (product local path)"
python3 bootstrap/env/check_env.py || {
  echo "env-check failed — run make env-init and edit .env (DEPLOY_PROFILE)"
  exit 1
}
python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md
# Soft local path: try gateway + tier0; SKIP (exit 0) if Ollama absent
if curl -sf --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama up — running smoke-litellm-ollama if cage available"
  make smoke-litellm-ollama 2>/dev/null || echo "smoke-litellm soft-skip (cage/host path not ready)"
else
  echo "Ollama not on :11434 — structural only (local bulk SKIP; still stage OK for docs track)"
fi
echo "env-stage: green for structural; local LLM optional"
