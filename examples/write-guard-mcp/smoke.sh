#!/usr/bin/env bash
# Thin wrapper → root Make target (GAP-05/25)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
exec make smoke-write-guard
