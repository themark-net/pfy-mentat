#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
mkdir -p pipelines/smoke/asm
OUT=pipelines/smoke/asm/results.latest.md
echo "# asm smoke" >"$OUT"
if ! command -v node >/dev/null 2>&1; then
  echo "status: soft-skip (no node)" | tee -a "$OUT"
  exit 0
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "status: soft-skip (no npm)" | tee -a "$OUT"
  exit 0
fi
if ! command -v asm >/dev/null 2>&1 && ! npx --yes asm --help >/dev/null 2>&1; then
  echo "status: soft-skip (asm not installed; pattern-only OK)" | tee -a "$OUT"
  exit 0
fi
echo "status: cli-present" | tee -a "$OUT"
exit 0
