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
# Prefer direct host path (NO_PROXY) so mitm does not need to resolve host.docker.internal.
# If proxy is required, coding-agent-local must whitelist host.docker.internal and
# compose must set extra_hosts: host.docker.internal:host-gateway (make local-ollama-up).
if ! getent hosts host.docker.internal >/dev/null 2>&1; then
  echo "error: host.docker.internal does not resolve in this container." >&2
  echo "  fix: make local-ollama-up   # applies overlays/local-ollama extra_hosts" >&2
  exit 1
fi
HTTP_CODE=$(curl -sS -m 15 -o /tmp/ollama-tags-cage.json -w "%{http_code}" \
  --noproxy host.docker.internal,localhost,127.0.0.1 \
  "${HOST_ROOT}/api/tags" || true)
if [[ ! -s /tmp/ollama-tags-cage.json ]]; then
  echo "error: empty response from ${HOST_ROOT}/api/tags (http=${HTTP_CODE})" >&2
  echo "  host: ./examples/litellm-ollama/host-ollama-gateway.sh status" >&2
  echo "  host: curl -sS http://127.0.0.1:11435/api/tags | head" >&2
  exit 1
fi
if ! python3 -c 'import json; json.load(open("/tmp/ollama-tags-cage.json"))' 2>/dev/null; then
  echo "error: non-JSON from ${HOST_ROOT}/api/tags (http=${HTTP_CODE}) — often mitm 502 when DNS/policy fails" >&2
  head -c 400 /tmp/ollama-tags-cage.json >&2 || true
  echo "" >&2
  echo "  fix: make local-ollama-up && make smoke-litellm-ollama" >&2
  echo "  ensure policy coding-agent-local allows host.docker.internal" >&2
  exit 1
fi
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
        print("error: model not present on host Ollama — ollama pull " + want, file=sys.stderr)
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
