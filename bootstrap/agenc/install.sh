#!/usr/bin/env bash
# Install official AgenC CLI + runtime (tetsuo-ai).
#
# Official sources:
#   https://get.agenc.ag/install.sh
#   npm install -g @tetsuo-ai/agenc
#   docs: https://github.com/tetsuo-ai/agenc-core/blob/main/docs/install.md
#
# Requires Node.js >= 25 (upstream). If system Node is older, this helper can
# fetch a user-local Node 25 under ~/.local/share/pfy-mentat/node (no root).
set -euo pipefail

MIN_NODE_MAJOR="${AGENC_MIN_NODE_MAJOR:-25}"
PREFIX="${AGENC_INSTALL_PREFIX:-$HOME/.local}"
AGENC_HOME="${AGENC_HOME:-$HOME/.agenc}"
NODE_CACHE="${AGENC_NODE_CACHE:-$HOME/.local/share/pfy-mentat/node}"
METHOD="${AGENC_INSTALL_METHOD:-official}"  # official | npm
INSTALL_DAEMON="${AGENC_INSTALL_DAEMON:-0}"  # 0 = --no-daemon (safer for smoke/labs)
PIN_VERSION="${AGENC_VERSION:-}"             # empty = latest

log() { printf 'agenc-install: %s\n' "$*" >&2; }
fail() { log "ERROR: $*"; exit 1; }

node_major() {
  command -v node >/dev/null 2>&1 || { echo 0; return; }
  node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))' 2>/dev/null || echo 0
}

ensure_node() {
  local major
  major="$(node_major)"
  if [[ "$major" -ge "$MIN_NODE_MAJOR" ]]; then
    log "Node $(node -v) OK (>= ${MIN_NODE_MAJOR})"
    return 0
  fi
  log "system Node is $(command -v node >/dev/null && node -v || echo 'missing'); need >= ${MIN_NODE_MAJOR}"
  if [[ "${AGENC_BOOTSTRAP_NODE:-1}" != "1" ]]; then
    fail "set PATH to Node ${MIN_NODE_MAJOR}+ or AGENC_BOOTSTRAP_NODE=1 (default) to fetch user-local Node"
  fi

  local os arch platform tarball url dest
  case "$(uname -s)" in
    Linux) os=linux ;;
    Darwin) os=darwin ;;
    *) fail "unsupported OS for Node bootstrap: $(uname -s)" ;;
  esac
  case "$(uname -m)" in
    x86_64|amd64) arch=x64 ;;
    aarch64|arm64) arch=arm64 ;;
    *) fail "unsupported arch for Node bootstrap: $(uname -m)" ;;
  esac
  # Pin a known-good Node 25.x from nodejs.org (override with AGENC_NODE_VERSION)
  local ver="${AGENC_NODE_VERSION:-v25.9.0}"
  platform="node-${ver}-${os}-${arch}"
  dest="${NODE_CACHE}/${ver}"
  if [[ ! -x "${dest}/bin/node" ]]; then
    mkdir -p "$NODE_CACHE"
    tarball="/tmp/${platform}.tar.xz"
    url="https://nodejs.org/dist/${ver}/${platform}.tar.xz"
    log "downloading Node ${ver} → ${dest}"
    curl -fsSL "$url" -o "$tarball"
    mkdir -p "$dest"
    tar -xJf "$tarball" -C "$NODE_CACHE"
    # tarball extracts to node-vXX-os-arch/
    rm -rf "$dest"
    mv "${NODE_CACHE}/${platform}" "$dest"
    rm -f "$tarball"
  fi
  export PATH="${dest}/bin:${PATH}"
  log "using bootstrapped Node $(node -v) from ${dest}/bin"
  [[ "$(node_major)" -ge "$MIN_NODE_MAJOR" ]] || fail "bootstrap Node still too old"
}

install_official() {
  local args=()
  [[ -n "$PIN_VERSION" ]] && args+=(--version "$PIN_VERSION")
  args+=(--prefix "$PREFIX")
  [[ "$INSTALL_DAEMON" == "0" ]] && args+=(--no-daemon)
  log "running official installer (get.agenc.ag) prefix=${PREFIX} daemon=${INSTALL_DAEMON}"
  # shellcheck disable=SC2086
  curl -fsSL https://get.agenc.ag/install.sh | sh -s -- "${args[@]}"
}

install_npm() {
  command -v npm >/dev/null 2>&1 || fail "npm required for AGENC_INSTALL_METHOD=npm"
  local pkg="@tetsuo-ai/agenc"
  [[ -n "$PIN_VERSION" ]] && pkg="${pkg}@${PIN_VERSION}"
  log "npm install -g ${pkg}"
  npm install -g "$pkg"
}

main() {
  ensure_node
  case "$METHOD" in
    official|curl|sh) install_official ;;
    npm) install_npm ;;
    *) fail "unknown AGENC_INSTALL_METHOD=$METHOD (official|npm)" ;;
  esac

  export PATH="${PREFIX}/bin:${PATH}"
  if ! command -v agenc >/dev/null 2>&1; then
    fail "agenc not on PATH after install (expected ${PREFIX}/bin/agenc). Add ${PREFIX}/bin to PATH."
  fi
  log "installed: $(command -v agenc)"
  agenc --help >/dev/null 2>&1 || agenc help >/dev/null 2>&1 || true
  log "AGENC_HOME=${AGENC_HOME}"
  log "next: make agenc-smoke"
}

main "$@"
