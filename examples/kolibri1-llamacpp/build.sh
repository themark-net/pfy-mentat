#!/usr/bin/env bash
# Build llama.cpp @ pinned rev + community kolibri1 patch into $KOLIBRI_RUNTIME_DIR (gitignored tmp).
# KOLIBRI_BACKEND=cpu (default) or vulkan (needs Vulkan headers + glslc; not on nimo by default).
set -euo pipefail
source "$(dirname "$0")/env.sh"
mkdir -p "$KOLIBRI_RUNTIME_DIR" && cd "$KOLIBRI_RUNTIME_DIR"
[ -f kolibri1-runtime.patch ] || curl -fsSL -o kolibri1-runtime.patch \
  "https://huggingface.co/$KOLIBRI_HF_REPO/resolve/main/runtime-source/kolibri1-runtime.patch"
if [ ! -d llama.cpp ]; then
  git init -q llama.cpp
  git -C llama.cpp remote add origin https://github.com/ggml-org/llama.cpp.git
  git -C llama.cpp fetch -q --depth 1 origin "$KOLIBRI_LLAMA_CPP_REV"
  git -C llama.cpp checkout -q FETCH_HEAD
  git -C llama.cpp apply --check ../kolibri1-runtime.patch
  git -C llama.cpp apply ../kolibri1-runtime.patch
fi
vk=OFF; [ "$KOLIBRI_BACKEND" = vulkan ] && vk=ON
cmake -S llama.cpp -B "build-$KOLIBRI_BACKEND" -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=OFF -DGGML_BLAS=OFF -DGGML_VULKAN=$vk -DLLAMA_CURL=OFF
cmake --build "build-$KOLIBRI_BACKEND" --config Release --parallel "$(nproc)" --target llama-server llama-cli
"build-$KOLIBRI_BACKEND/bin/llama-server" --version
echo "BUILD_OK $KOLIBRI_RUNTIME_DIR/build-$KOLIBRI_BACKEND"
