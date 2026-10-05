#!/usr/bin/env bash
# Foreground llama-server for the patched kolibri1 build (localhost only).
set -euo pipefail
source "$(dirname "$0")/env.sh"
[ -x "$KOLIBRI_LLAMA_SERVER" ] || { echo "FAIL: no patched llama-server at $KOLIBRI_LLAMA_SERVER (run build.sh)"; exit 2; }
[ "$(stat -c %s "$KOLIBRI_GGUF" 2>/dev/null || echo 0)" -eq "$KOLIBRI_GGUF_BYTES" ] || { echo "FAIL: GGUF missing/incomplete at $KOLIBRI_GGUF (run download.sh)"; exit 2; }
ngl=0; [ "$KOLIBRI_BACKEND" = vulkan ] && ngl=99
exec "$KOLIBRI_LLAMA_SERVER" -m "$KOLIBRI_GGUF" --alias Kolibri-1-Q3_K_S -ngl $ngl \
  -c "${KOLIBRI_CTX:-8192}" --cache-type-k q8_0 --cache-type-v q8_0 -fa on \
  --host 127.0.0.1 --port "$KOLIBRI_PORT" --parallel 1 --jinja --no-warmup \
  --temp 1.0 --top-p 0.97 --top-k 128 "$@"
