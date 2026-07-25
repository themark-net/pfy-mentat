#!/usr/bin/env bash
# Dual-access permissions for the host-side Grok session store.
#
# Problem: docker exec "chown -R agent:agent …/sessions" and docker cp leave
# ~/.agentcage/grok-state/sessions owned by uid 1001 mode 700. Host Make then
# fails with Permission denied (mkdir for import, etc.).
#
# Model:
#   grok-state/          0700 host:host — only operator traverses
#   grok-state/sessions/ a+rwX          — host + cage agent both write
#   grok-home/auth.json  agent 0600     — handled by grok-auth-import
#
# Prefers docker root on the bind mount (no host sudo). Falls back to host
# chmod/chown/sudo when the container is down.
#
# Usage: fix-grok-state-perms.sh [AGENTCAGE_DIR]
set -euo pipefail

AGENTCAGE_DIR="${1:-${AGENTCAGE_DIR:-$HOME/.agentcage}}"
STATE="${AGENTCAGE_DIR}/grok-state"
SESSIONS="${STATE}/sessions"
HOST_UID="${SUDO_UID:-$(id -u)}"
HOST_GID="${SUDO_GID:-$(id -g)}"
if [[ -n "${SUDO_USER:-}" ]]; then
  HOST_UID=$(id -u "$SUDO_USER")
  HOST_GID=$(id -g "$SUDO_USER")
fi

mkdir -p "$STATE"
# Parent must stay private to the host operator
chmod 700 "$STATE" 2>/dev/null || true

# Ensure sessions dir exists even if we cannot yet write inside it
if [[ ! -d "$SESSIONS" ]]; then
  mkdir -p "$SESSIONS" 2>/dev/null || true
fi

fix_via_docker() {
  docker inspect agent-cage-agent --format '{{.State.Status}}' 2>/dev/null | grep -q running || return 1
  # Bind mount: chmod/chown inside container changes host inode metadata.
  docker exec -u root agent-cage-agent bash -lc '
    set -e
    if [ ! -d /home/agent/.grok/sessions ]; then
      mkdir -p /home/agent/.grok/sessions
    fi
    # Open tree for host uid 1000 and agent 1001 (parent grok-state stays 700 on host)
    chmod 777 /home/agent/.grok/sessions
    find /home/agent/.grok/sessions -type d -exec chmod 777 {} +
    find /home/agent/.grok/sessions -type f -exec chmod a+rw {} +
    # Optional: align ownership to first non-root host-looking uid if present as env
    if [ -n "'"${HOST_UID}"'" ] && [ -n "'"${HOST_GID}"'" ]; then
      chown -R "'"${HOST_UID}:${HOST_GID}"'" /home/agent/.grok/sessions 2>/dev/null || true
      # Agent still needs write: keep open mode after chown
      chmod 777 /home/agent/.grok/sessions
      find /home/agent/.grok/sessions -type d -exec chmod 777 {} + 2>/dev/null || true
      find /home/agent/.grok/sessions -type f -exec chmod a+rw {} + 2>/dev/null || true
    fi
  '
}

fix_via_host() {
  if [[ ! -d "$SESSIONS" ]]; then
    mkdir -p "$SESSIONS" || sudo mkdir -p "$SESSIONS"
  fi
  if chown -R "$HOST_UID:$HOST_GID" "$SESSIONS" 2>/dev/null; then
    :
  elif command -v sudo >/dev/null 2>&1; then
    sudo chown -R "$HOST_UID:$HOST_GID" "$SESSIONS"
  else
    return 1
  fi
  chmod 777 "$SESSIONS" 2>/dev/null || sudo chmod 777 "$SESSIONS"
  find "$SESSIONS" -type d -exec chmod 777 {} + 2>/dev/null || true
  find "$SESSIONS" -type f -exec chmod a+rw {} + 2>/dev/null || true
}

if fix_via_docker; then
  method=docker
elif fix_via_host; then
  method=host
else
  echo "error: cannot fix $SESSIONS (start agent container or sudo chown -R $(id -u) $SESSIONS)" >&2
  exit 1
fi

# Ensure dir exists for host after docker-created path
mkdir -p "$SESSIONS" 2>/dev/null || true

probe="$SESSIONS/.pfy-write-probe-$$"
if ! touch "$probe" 2>/dev/null; then
  echo "error: host still cannot write $SESSIONS after $method fix" >&2
  ls -la "$STATE" >&2 || true
  ls -la "$SESSIONS" >&2 || true
  exit 1
fi
rm -f "$probe"

echo "fix-grok-state-perms: OK ($method)  $SESSIONS"
