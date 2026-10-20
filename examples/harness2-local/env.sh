#!/usr/bin/env bash
# Source me. Tool caches and XDG dirs live under $W/tmp/state.
# HOME is not modified. UV_PYTHON_DOWNLOADS=never: no Python download.
if [[ -z "${BASH_SOURCE:-}" ]]; then
  echo "env.sh must be sourced from bash" >&2
  return 1 2>/dev/null || exit 1
fi
_H2L_HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
W="${HARNESS2_W:-$(cd "$_H2L_HERE/../.." && pwd)}"
export HARNESS2_W="$W"
_H2L_STATE="$W/tmp/state"
export UV_CACHE_DIR="$_H2L_STATE/uv-cache"
export UV_PYTHON_INSTALL_DIR="$_H2L_STATE/uv-python"
export UV_PYTHON_BIN_DIR="$_H2L_STATE/uv-bin"
export UV_TOOL_DIR="$_H2L_STATE/uv-tools"
export UV_PYTHON_DOWNLOADS=never
export npm_config_cache="$_H2L_STATE/npm-cache"
export npm_config_update_notifier=false
export BUN_INSTALL_CACHE_DIR="$_H2L_STATE/bun-cache"
export BUN_INSTALL="$_H2L_STATE/bun"
export XDG_CONFIG_HOME="$_H2L_STATE/xdg-config"
export XDG_CACHE_HOME="$_H2L_STATE/xdg-cache"
# Caller wins. Upstream Proposer and the executor launcher set these to the
# workspace. The state dir is read-only inside the sandbox, so forcing it
# here makes OpenCode's mkdir fail with EROFS.
: "${XDG_DATA_HOME:=$_H2L_STATE/xdg-data}"
: "${XDG_STATE_HOME:=$_H2L_STATE/xdg-state}"
export XDG_DATA_HOME XDG_STATE_HOME
export OPENCODE_CONFIG="$_H2L_STATE/opencode.json"
unset _H2L_HERE _H2L_STATE
