#!/usr/bin/env bash
# env-promote — dev → stage → main helpers for pfy-mentat
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

die() { echo "error: $*" >&2; exit 1; }
need_clean() {
  if [[ -n "$(git status --porcelain)" ]]; then
    die "working tree not clean; commit or stash first"
  fi
}

cmd_status() {
  git fetch origin --prune 2>/dev/null || true
  echo "=== branch promotion status ==="
  for b in main stage dev; do
    if git rev-parse --verify "origin/$b" >/dev/null 2>&1; then
      sha=$(git rev-parse --short "origin/$b")
      echo "  origin/$b  $sha"
    elif git rev-parse --verify "$b" >/dev/null 2>&1; then
      sha=$(git rev-parse --short "$b")
      echo "  local/$b   $sha  (not on origin yet)"
    else
      echo "  $b         MISSING"
    fi
  done
  if git rev-parse --verify origin/main >/dev/null 2>&1 && git rev-parse --verify origin/stage >/dev/null 2>&1; then
    if [[ "$(git rev-parse origin/main)" == "$(git rev-parse origin/stage)" ]]; then
      echo "stage == main (clean production mirror)"
    else
      echo "stage != main (upgrade rehearsal or drift — inspect before to-main)"
      git log --oneline origin/main..origin/stage | head -10 || true
    fi
  fi
  if git rev-parse --verify origin/dev >/dev/null 2>&1 && git rev-parse --verify origin/stage >/dev/null 2>&1; then
    n=$(git rev-list --count origin/stage..origin/dev 2>/dev/null || echo 0)
    echo "commits on dev not in stage: $n"
  fi
}

cmd_to_stage() {
  need_clean
  git fetch origin
  git checkout stage
  git pull --ff-only origin stage 2>/dev/null || git reset --hard origin/main
  git merge --no-ff origin/dev -m "promote: dev → stage (upgrade rehearsal)"
  git push origin stage
  echo "promoted dev → stage. Run acceptance (eval-structural, smokes) before to-main."
}

cmd_to_main() {
  need_clean
  local tag=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tag) tag="${2:-}"; shift 2 ;;
      *) die "unknown arg: $1" ;;
    esac
  done
  git fetch origin
  git checkout main
  git pull --ff-only origin main
  git merge --no-ff origin/stage -m "release: stage → main (accepted)"
  if [[ -n "$tag" ]]; then
    git tag -a "$tag" -m "release $tag"
  fi
  # Fresh verify
  if [[ -f Makefile ]] && grep -q '^eval-structural' Makefile; then
    make eval-structural || die "eval-structural failed — fix before push"
  fi
  git push origin main
  [[ -n "$tag" ]] && git push origin "$tag"
  # Resync stage from main
  git checkout stage
  git reset --hard origin/main
  git push --force-with-lease origin stage
  git checkout dev
  git merge --ff-only origin/main || git merge origin/main -m "chore: merge main into dev after release"
  git push origin dev 2>/dev/null || true
  echo "released stage → main${tag:+ ($tag)}; stage resynced from main"
}

cmd_sync_stage() {
  need_clean
  git fetch origin
  git checkout stage
  git reset --hard origin/main
  git push --force-with-lease origin stage
  echo "stage := main"
}

usage() {
  cat <<'U'
env-promote — pfy-mentat branch promotion (ADR-0014)

  status       Show main/stage/dev SHAs and drift
  to-stage     Merge origin/dev into stage (upgrade rehearsal)
  to-main [--tag vX.Y.Z]   Accept stage → main, tag, resync stage, update dev
  sync-stage   Force stage := main
U
}

main() {
  local c="${1:-status}"
  shift || true
  case "$c" in
    status) cmd_status ;;
    to-stage) cmd_to_stage ;;
    to-main) cmd_to_main "$@" ;;
    sync-stage) cmd_sync_stage ;;
    help|-h|--help) usage ;;
    *) usage; die "unknown: $c" ;;
  esac
}
main "$@"
