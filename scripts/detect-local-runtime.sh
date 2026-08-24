#!/usr/bin/env bash
# Probe pluggable OpenAI-compatible local inference (ADR-0014).
# Prints one JSON object: {"engine","base_url","status"}
# Detect order: llama-swap | llama-server | shimmy | ollama
# Override: PFY_LOCAL_RUNTIME, LOCAL_OPENAI_BASE_URL
# Never vendors engines; missing is honest (not fake-healthy).
set -euo pipefail

have() { command -v "$1" >/dev/null 2>&1; }

emit() {
  python3 -c 'import json,sys; print(json.dumps({"engine":sys.argv[1],"base_url":sys.argv[2],"status":sys.argv[3]}))' "$1" "$2" "$3"
}

http_ok() {
  curl -sf --max-time 1 "$1" >/dev/null 2>&1
}

probe() {
  local base="${1%/}"
  http_ok "$base/v1/models" && return 0
  http_ok "$base/health" && return 0
  http_ok "$base/api/tags" && return 0
  return 1
}

if [[ -n "${LOCAL_OPENAI_BASE_URL:-}" ]]; then
  eng="${PFY_LOCAL_RUNTIME:-openai-compat}"
  base="${LOCAL_OPENAI_BASE_URL%/}"
  if probe "$base"; then emit "$eng" "$base" "ready"; else emit "$eng" "$base" "partial"; fi
  exit 0
fi

if [[ -n "${PFY_LOCAL_RUNTIME:-}" ]]; then
  case "$PFY_LOCAL_RUNTIME" in
    llama-swap) bases=(http://127.0.0.1:8080 http://127.0.0.1:9292) ;;
    llama-server|llama.cpp) bases=(http://127.0.0.1:8080) ;;
    shimmy) bases=(http://127.0.0.1:11435) ;;
    ollama) bases=(http://127.0.0.1:11434) ;;
    *) bases=(http://127.0.0.1:8080) ;;
  esac
  for b in "${bases[@]}"; do
    if probe "$b"; then emit "$PFY_LOCAL_RUNTIME" "$b" "ready"; exit 0; fi
  done
  emit "$PFY_LOCAL_RUNTIME" "${bases[0]}" "partial"
  exit 0
fi

# 1. llama-swap (PATH first, then common HTTP)
if have llama-swap; then
  for b in http://127.0.0.1:8080 http://127.0.0.1:9292; do
    if probe "$b"; then emit "llama-swap" "$b" "ready"; exit 0; fi
  done
  emit "llama-swap" "http://127.0.0.1:8080" "partial"
  exit 0
fi

# 2. llama.cpp llama-server
if have llama-server; then
  if probe "http://127.0.0.1:8080"; then emit "llama-server" "http://127.0.0.1:8080" "ready"; exit 0; fi
  emit "llama-server" "http://127.0.0.1:8080" "partial"
  exit 0
fi
if probe "http://127.0.0.1:8080"; then
  emit "llama-server" "http://127.0.0.1:8080" "ready"
  exit 0
fi

# 3. Shimmy (often :11435)
if have shimmy; then
  if probe "http://127.0.0.1:11435"; then emit "shimmy" "http://127.0.0.1:11435" "ready"; exit 0; fi
  emit "shimmy" "http://127.0.0.1:11435" "partial"
  exit 0
fi
if probe "http://127.0.0.1:11435"; then
  emit "shimmy" "http://127.0.0.1:11435" "ready"
  exit 0
fi

# 4. Ollama adapter (T-0101)
if have ollama; then
  if probe "http://127.0.0.1:11434"; then emit "ollama" "http://127.0.0.1:11434" "ready"; exit 0; fi
  emit "ollama" "http://127.0.0.1:11434" "partial"
  exit 0
fi
if probe "http://127.0.0.1:11434"; then
  emit "ollama" "http://127.0.0.1:11434" "ready"
  exit 0
fi

emit "none" "" "missing"
