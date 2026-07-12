#!/usr/bin/env bash
# Run inside agent-cage agent container (or via make smoke-litellm-ollama).
set -euo pipefail

MODEL="${LITELLM_SMOKE_MODEL:-deepseek-coder:latest}"
BASE="${OPENAI_BASE_URL:-http://host.docker.internal:11435/v1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${LITELLM_VENV:-/workspace/.venvs/litellm-smoke}"

echo "== litellm-ollama in-cage smoke =="
echo "  OPENAI_BASE_URL=$BASE"
echo "  LITELLM_SMOKE_MODEL=$MODEL"
echo "  VENV=$VENV_DIR"

HOST_ROOT="${BASE%/v1}"
echo "== preflight: GET ${HOST_ROOT}/api/tags =="
curl -sS -m 15 "${HOST_ROOT}/api/tags" -o /tmp/ollama-tags-cage.json
python3 - <<PY
import json, os, sys
d = json.load(open("/tmp/ollama-tags-cage.json"))
names = [m.get("name") for m in (d.get("models") or [])]
want = os.environ.get("LITELLM_SMOKE_MODEL", "deepseek-coder:latest")
print(f"  have {len(names)} models; want {want!r}:", "yes" if want in names else "NO")
if want not in names:
    base = want.split(":")[0]
    alt = [n for n in names if n and n.startswith(base)]
    if not alt:
        print("error: model not present on host Ollama", file=sys.stderr)
        sys.exit(1)
    print("  note: exact tag missing; closest:", alt[:5])
PY

echo "== ensure venv + litellm =="
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  mkdir -p "$(dirname "$VENV_DIR")"
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install -q --upgrade pip
python -c "import litellm" 2>/dev/null || python -m pip install -q "litellm>=1.40.0"

echo "== LiteLLM completion =="
export OPENAI_BASE_URL="$BASE"
export LITELLM_SMOKE_MODEL="$MODEL"
python "${SCRIPT_DIR}/smoke_completion.py"
