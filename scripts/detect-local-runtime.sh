#!/usr/bin/env bash
# Probe local OpenAI-compatible inference. First healthy wins.
# Override: PFY_LOCAL_RUNTIME=llama-swap|llama-server|shimmy|ollama
#           LOCAL_OPENAI_BASE_URL=http://127.0.0.1:PORT/v1
set -euo pipefail
have() { command -v "$1" >/dev/null 2>&1; }
http_ok() { curl -sf --max-time 1 "$1" >/dev/null 2>&1; }

prefer="${PFY_LOCAL_RUNTIME:-}"
forced_url="${LOCAL_OPENAI_BASE_URL:-}"

probe() {
  local id="$1" url="$2" bin="$3" extra_url="${4:-}"
  local bin_ok=0 http=0
  have "$bin" && bin_ok=1
  if [[ -n "$url" ]] && http_ok "$url"; then http=1; fi
  if [[ -n "$extra_url" ]] && http_ok "$extra_url"; then http=1; url="$extra_url"; fi
  local status="missing"
  if [[ "$http" -eq 1 ]]; then status="ready"
  elif [[ "$bin_ok" -eq 1 ]]; then status="partial"
  fi
  printf '%s\t%s\t%s\n' "$id" "$status" "$url"
}

# id, models-or-health url, binary, openai url (optional)
rows=()
rows+=("$(probe llama-swap http://127.0.0.1:8080/v1/models llama-swap http://127.0.0.1:9292/v1/models)")
rows+=("$(probe llama-server http://127.0.0.1:8080/v1/models llama-server)")
rows+=("$(probe shimmy http://127.0.0.1:11435/v1/models shimmy)")
rows+=("$(probe ollama http://127.0.0.1:11434/api/tags ollama)")

pick_id="" pick_status="missing" pick_url=""
if [[ -n "$prefer" ]]; then
  for line in "${rows[@]}"; do
    IFS=$'\t' read -r id st url <<<"$line"
    if [[ "$id" == "$prefer" ]]; then pick_id="$id"; pick_status="$st"; pick_url="$url"; break; fi
  done
else
  for line in "${rows[@]}"; do
    IFS=$'\t' read -r id st url <<<"$line"
    if [[ "$st" == "ready" ]]; then pick_id="$id"; pick_status="$st"; pick_url="$url"; break; fi
  done
  if [[ -z "$pick_id" ]]; then
    for line in "${rows[@]}"; do
      IFS=$'\t' read -r id st url <<<"$line"
      if [[ "$st" == "partial" ]]; then pick_id="$id"; pick_status="$st"; pick_url="$url"; break; fi
    done
  fi
fi
[[ -n "$pick_id" ]] || { pick_id="none"; pick_status="missing"; pick_url=""; }

base="$forced_url"
if [[ -z "$base" ]]; then
  case "$pick_id" in
    llama-swap) base="http://127.0.0.1:8080/v1" ;;
    llama-server) base="http://127.0.0.1:8080/v1" ;;
    shimmy) base="http://127.0.0.1:11435/v1" ;;
    ollama) base="http://127.0.0.1:11434/v1" ;;
    *) base="" ;;
  esac
fi

if [[ "${1:-}" == "--json" ]]; then
  python3 - "$pick_id" "$pick_status" "$base" <<'PY'
import json,sys
print(json.dumps({"engine":sys.argv[1],"status":sys.argv[2],"base_url":sys.argv[3]}))
PY
else
  echo "engine=$pick_id status=$pick_status base_url=$base"
fi
