#!/usr/bin/env bash
# Product lever 1: onboard — attach process kit + env example to a project.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${DIR:-${1:-.}}"
DIR="$(cd "$DIR" && pwd)"
echo "==> project-onboard → $DIR"
if [[ -x "$ROOT/bootstrap/project-process/init.sh" ]]; then
  (cd "$DIR" && bash "$ROOT/bootstrap/project-process/init.sh" . || true)
else
  echo "warn: bootstrap/project-process/init.sh missing"
fi
if [[ ! -f "$DIR/.env" && -f "$ROOT/bootstrap/env/env.example" ]]; then
  cp "$ROOT/bootstrap/env/env.example" "$DIR/.env"
  echo "created $DIR/.env from env.example (edit secrets)"
fi
echo "onboard: process scaffold + .env example done"
echo "next: make env-stage   then work your product code"
