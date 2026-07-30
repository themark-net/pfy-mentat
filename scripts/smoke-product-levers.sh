#!/usr/bin/env bash
# GAP-09 dual-sided product onboard smoke
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p pipelines/smoke/product-levers
OUT=pipelines/smoke/product-levers/results.latest.md
TMP=$(mktemp -d /tmp/pfy-product-XXXXXX)
trap 'rm -rf "$TMP"' EXIT
{
  echo "# Product levers smoke"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "tmp: $TMP"
} >"$OUT"
chmod +x scripts/product-onboard.sh
DIR="$TMP" ./scripts/product-onboard.sh "$TMP" | tee -a "$OUT"
python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md
echo "status: pass (onboard tmp + structural)" | tee -a "$OUT"
echo "smoke-product-levers: PASS"
