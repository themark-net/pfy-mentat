#!/usr/bin/env bash
# Product lever 3: ship — verify structural + optional push of PRODUCT remote.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> product-ship"
python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md
python3 examples/eval-harness/run_golden.py --write-md pipelines/eval/golden.latest.md || true
if [[ -n "${PRODUCT_REMOTE:-}" ]]; then
  BRANCH="${PRODUCT_BRANCH:-main}"
  echo "pushing PRODUCT_REMOTE=$PRODUCT_REMOTE branch=$BRANCH"
  git push "$PRODUCT_REMOTE" "HEAD:refs/heads/$BRANCH"
else
  echo "PRODUCT_REMOTE unset — verified only (no push)."
  echo "Set PRODUCT_REMOTE=origin (or product remote) to push product code."
fi
echo "product-ship: done"
