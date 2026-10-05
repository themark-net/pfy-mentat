# Shared paths for the Kolibri-1 llama.cpp lab (sourced by build/download/serve).
# Defaults resolve to the canonical checkout's gitignored tmp/ (works from worktrees too).
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_common="$(git -C "$_here" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || echo "$_here/../../.git")"
PFY_MAIN_ROOT="${PFY_MAIN_ROOT:-$(cd "$_common/.." && pwd)}"
KOLIBRI_RUNTIME_DIR="${KOLIBRI_RUNTIME_DIR:-$PFY_MAIN_ROOT/tmp/kolibri-runtime}"
KOLIBRI_MODEL_DIR="${KOLIBRI_MODEL_DIR:-$PFY_MAIN_ROOT/tmp/models/Kolibri-1-Q3_K_S-GGUF}"
KOLIBRI_GGUF="${KOLIBRI_GGUF:-$KOLIBRI_MODEL_DIR/Kolibri-1-Q3_K_S.gguf}"
KOLIBRI_BACKEND="${KOLIBRI_BACKEND:-cpu}"   # cpu | vulkan
KOLIBRI_LLAMA_SERVER="${KOLIBRI_LLAMA_SERVER:-$KOLIBRI_RUNTIME_DIR/build-$KOLIBRI_BACKEND/bin/llama-server}"
KOLIBRI_PORT="${KOLIBRI_PORT:-8081}"
# Community port pins (Eliasfpv28/Kolibri-1-Q3_K_S-GGUF, unofficial, experimental)
KOLIBRI_HF_REPO="Eliasfpv28/Kolibri-1-Q3_K_S-GGUF"
KOLIBRI_LLAMA_CPP_REV="edd6e2bbdad5930899a93db8fa73c3b61c7b9bcc"
KOLIBRI_GGUF_BYTES=33870242400
KOLIBRI_GGUF_SHA256="26ce4a2f618e3d55d401faaa78bb144057268b8303e645b6e3d552258d1d34aa"
export KOLIBRI_GGUF_BYTES KOLIBRI_GGUF_SHA256 PFY_MAIN_ROOT KOLIBRI_RUNTIME_DIR KOLIBRI_MODEL_DIR KOLIBRI_GGUF KOLIBRI_BACKEND KOLIBRI_LLAMA_SERVER KOLIBRI_PORT
