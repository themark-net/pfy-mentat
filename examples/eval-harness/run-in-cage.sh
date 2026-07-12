#!/usr/bin/env bash
# Tier-1 scored task inside agent-cage (LiteLLM → host Ollama).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK="${EVAL_TASK:-001-is-palindrome}"
BASE="${OPENAI_BASE_URL:-http://host.docker.internal:11435/v1}"
# Prefer EVAL_MODEL (scored task); fall back to LITELLM_SMOKE_MODEL then qwen2.5:14b
MODEL="${EVAL_MODEL:-${LITELLM_SMOKE_MODEL:-qwen2.5:14b}}"
VENV="${EVAL_VENV:-/workspace/.venvs/eval-harness}"

echo "== eval-harness tier1 =="
echo "  task=$TASK base=$BASE model=$MODEL"

HOST_ROOT="${BASE%/v1}"
curl -sS -m 15 "${HOST_ROOT}/api/tags" -o /tmp/ollama-tags-eval.json
python3 - <<PY
import json, os, sys
d = json.load(open("/tmp/ollama-tags-eval.json"))
names = [m.get("name") for m in (d.get("models") or [])]
want = os.environ.get("EVAL_MODEL") or os.environ.get("LITELLM_SMOKE_MODEL", "qwen2.5:14b")
if want not in names:
    print(f"error: model {want!r} not on Ollama", file=sys.stderr)
    sys.exit(2)
print(f"  ollama models: {len(names)}; {want}: yes")
PY

if [[ ! -x "${VENV}/bin/python" ]]; then
  mkdir -p "$(dirname "$VENV")"
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
python -m pip install -q --upgrade pip
python -c "import litellm" 2>/dev/null || python -m pip install -q "litellm>=1.40.0"

export OPENAI_BASE_URL="$BASE"
export EVAL_MODEL="$MODEL"
export LITELLM_SMOKE_MODEL="$MODEL"
export EVAL_RESULT_JSON="${EVAL_RESULT_JSON:-/tmp/eval-tier1-result.json}"
python "${SCRIPT_DIR}/run_scored_task.py" --task "$TASK" --tasks-root "${SCRIPT_DIR}/tasks"
