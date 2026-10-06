#!/usr/bin/env bash
# Ollama-bundled llama-server + ROCm HIP, --no-mmap (avoid host-page-cache + GTT double hold).
# Env: GGML_BACKEND_PATH must be the .so file (dir alone fails). HSA_OVERRIDE_GFX_VERSION=11.5.1 for Strix Halo.
# GGML_CUDA_ENABLE_UNIFIED_MEMORY=1 is the symbol exported by libggml-hip.so (CUDA-compat name on HIP builds).
set -euo pipefail
MODEL_PATH=${1:?gguf path}
PORT=${2:-18080}
CTX=${3:-4096}
export HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION:-11.5.1}
export GGML_BACKEND_PATH=/usr/local/lib/ollama/rocm_v7_2/libggml-hip.so
export LD_LIBRARY_PATH=/usr/local/lib/ollama/rocm_v7_2:/usr/local/lib/ollama:${LD_LIBRARY_PATH:-}
export GGML_CUDA_ENABLE_UNIFIED_MEMORY=${GGML_CUDA_ENABLE_UNIFIED_MEMORY:-1}
export GGML_HIP_UMA=${GGML_HIP_UMA:-1}
exec /usr/local/lib/ollama/llama-server \
  --model "$MODEL_PATH" \
  --host 127.0.0.1 --port "$PORT" \
  --no-mmap \
  -ngl 999 \
  -c "$CTX" \
  -np 1 \
  -fa on \
  --no-webui
