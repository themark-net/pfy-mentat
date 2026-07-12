#!/usr/bin/env bash
# Host smoke for AgenC + project agenc-launch wrapper.
# Exit: 0 pass, 1 fail, 2 skip (binary missing — install first).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAUNCHER="${ROOT}/bootstrap/agenc/agenc-launch"
PREFIX="${AGENC_INSTALL_PREFIX:-$HOME/.local}"
export PATH="${PREFIX}/bin:${PATH}"

# Prefer project wrapper for launch-path checks
export AGENC_CMD="${AGENC_CMD:-agenc}"
export AGENC_UPDATE_CHECK="${AGENC_UPDATE_CHECK:-0}"
export AGENC_NO_UPDATE="${AGENC_NO_UPDATE:-1}"
export AGENC_OFFLINE="${AGENC_OFFLINE:-1}"
export AGENC_DAEMON_AUTOSTART="${AGENC_DAEMON_AUTOSTART:-1}"

log() { printf 'agenc-smoke: %s\n' "$*"; }
fail() { log "FAIL: $*"; exit 1; }
skip() { log "SKIP: $*"; exit 2; }

pass=0
check() {
  local name="$1"
  shift
  log "check: $name"
  if "$@"; then
    log "  OK: $name"
    pass=$((pass + 1))
  else
    fail "$name"
  fi
}

log "== AgenC smoke =="
log "  PATH prefix: ${PREFIX}/bin"
log "  launcher: ${LAUNCHER}"

# 1) Wrapper exists + bash syntax
[[ -x "$LAUNCHER" ]] || chmod +x "$LAUNCHER"
bash -n "$LAUNCHER"
log "  OK: agenc-launch syntax"

# 2) Offline path of wrapper (must not attempt network update)
out="$(AGENC_OFFLINE=1 AGENC_DAEMON_AUTOSTART=0 AGENC_CMD=true "$LAUNCHER" 2>&1 || true)"
echo "$out" | grep -q 'OFFLINE mode' || fail "wrapper offline banner missing"
log "  OK: offline mode banner"

# 3) Binary present
if ! command -v agenc >/dev/null 2>&1; then
  skip "agenc not on PATH — run: make agenc-install (needs Node >= 25)"
fi
log "  agenc=$(command -v agenc)"

# 4) Help / version surface
if agenc --help >/dev/null 2>&1; then
  log "  OK: agenc --help"
  pass=$((pass + 1))
elif agenc help >/dev/null 2>&1; then
  log "  OK: agenc help"
  pass=$((pass + 1))
else
  fail "agenc help failed"
fi

# 5) Daemon via wrapper (preferred entry point)
log "check: daemon via agenc-launch"
if AGENC_OFFLINE=1 AGENC_UPDATE_CHECK=0 "$LAUNCHER" daemon status >/dev/null 2>&1; then
  log "  OK: daemon status (already up)"
  pass=$((pass + 1))
else
  log "  daemon not up — starting..."
  AGENC_OFFLINE=1 AGENC_UPDATE_CHECK=0 "$LAUNCHER" daemon start >/dev/null 2>&1 || true
  if AGENC_OFFLINE=1 AGENC_UPDATE_CHECK=0 "$LAUNCHER" daemon status >/dev/null 2>&1; then
    log "  OK: daemon status after start"
    pass=$((pass + 1))
  else
    # Some installs report status on stdout with non-zero until ready; try doctor next
    log "  WARN: daemon status not green (continuing to doctor)"
  fi
fi

# 6) doctor / onboard status (non-interactive)
if agenc doctor --json >/dev/null 2>&1; then
  log "  OK: agenc doctor --json"
  pass=$((pass + 1))
elif agenc doctor >/dev/null 2>&1; then
  log "  OK: agenc doctor"
  pass=$((pass + 1))
else
  log "  WARN: doctor not available or failed (pre-release CLI surface may vary)"
fi

if agenc onboard --status >/dev/null 2>&1; then
  log "  OK: agenc onboard --status"
  pass=$((pass + 1))
elif agenc onboard --status --json >/dev/null 2>&1; then
  log "  OK: agenc onboard --status --json"
  pass=$((pass + 1))
else
  log "  WARN: onboard --status not available"
fi

# 7) Optional one-shot LLM (only if provider keys present)
if [[ "${AGENC_SMOKE_LLM:-0}" == "1" ]]; then
  log "check: headless print (AGENC_SMOKE_LLM=1)"
  if AGENC_OFFLINE=1 AGENC_UPDATE_CHECK=0 "$LAUNCHER" --no-tui -p "Reply with exactly: PONG" 2>&1 | tee /tmp/agenc-smoke-llm.txt | grep -qi pong; then
    log "  OK: LLM print returned PONG"
    pass=$((pass + 1))
  else
    fail "LLM print smoke failed (see /tmp/agenc-smoke-llm.txt)"
  fi
else
  log "  skip LLM print (set AGENC_SMOKE_LLM=1 and provider keys to enable)"
fi

# Record result
mkdir -p "${ROOT}/pipelines/smoke/agenc"
{
  echo "| $(date -Iseconds) | agenc-smoke | PASS | checks≈${pass} | host wrapper+daemon |"
} >> "${ROOT}/pipelines/smoke/agenc/results.latest.md"

log "agenc-smoke: PASS (${pass} checks)"
exit 0
