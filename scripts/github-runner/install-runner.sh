#!/usr/bin/env bash
# Install a GitHub Actions self-hosted runner labeled for pfy-mentat.
# Safe default: runs as current user, workdir under $HOME/pfy-actions-runner.
#
# Prereq: create a registration token for this repo:
#   gh api -X POST repos/themark-net/pfy-mentat/actions/runners/registration-token --jq .token
#
# Usage:
#   export RUNNER_TOKEN=...
#   ./scripts/github-runner/install-runner.sh
#   ./scripts/github-runner/install-runner.sh --start
#
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/themark-net/pfy-mentat}"
RUNNER_DIR="${RUNNER_DIR:-$HOME/pfy-actions-runner}"
RUNNER_VERSION="${RUNNER_VERSION:-2.321.0}"
LABELS="${RUNNER_LABELS:-self-hosted,pfy-mentat,linux}"
START=0

for arg in "$@"; do
  case "$arg" in
    --start) START=1 ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
  esac
done

if [[ -z "${RUNNER_TOKEN:-}" ]]; then
  echo "ERROR: set RUNNER_TOKEN to a repo registration token" >&2
  echo "  export RUNNER_TOKEN=\"\$(gh api -X POST repos/themark-net/pfy-mentat/actions/runners/registration-token --jq .token)\"" >&2
  exit 1
fi

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

if [[ ! -f ./config.sh ]]; then
  arch="$(uname -m)"
  case "$arch" in
    x86_64) pkg_arch=x64 ;;
    aarch64|arm64) pkg_arch=arm64 ;;
    *) echo "Unsupported arch: $arch" >&2; exit 1 ;;
  esac
  tarball="actions-runner-linux-${pkg_arch}-${RUNNER_VERSION}.tar.gz"
  url="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${tarball}"
  echo "==> downloading $url"
  curl -fsSL -o "$tarball" "$url"
  tar xzf "$tarball"
  rm -f "$tarball"
fi

if [[ ! -f .runner ]]; then
  echo "==> configuring runner for $REPO_URL labels=$LABELS"
  ./config.sh --unattended \
    --url "$REPO_URL" \
    --token "$RUNNER_TOKEN" \
    --labels "$LABELS" \
    --name "${RUNNER_NAME:-pfy-$(hostname -s)}" \
    --work "_work" \
    --replace
fi

echo "==> runner directory: $RUNNER_DIR"
echo "    labels: $LABELS"
echo "    start once:   $RUNNER_DIR/run.sh"
echo "    install svc:  sudo $RUNNER_DIR/svc.sh install && sudo $RUNNER_DIR/svc.sh start"

if [[ "$START" -eq 1 ]]; then
  if [[ -x ./svc.sh ]] && command -v systemctl >/dev/null 2>&1; then
    sudo ./svc.sh install || true
    sudo ./svc.sh start
    echo "==> service started (svc.sh)"
  else
    nohup ./run.sh >/tmp/pfy-actions-runner.log 2>&1 &
    echo "==> run.sh backgrounded → /tmp/pfy-actions-runner.log"
  fi
fi
