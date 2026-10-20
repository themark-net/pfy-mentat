#!/usr/bin/env bash
# Pin harness2 and OpenCode under $W/tmp. No HOME writes. No harness2-setup.
# Usage: bash examples/harness2-local/stage.sh [--dry-run]
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=env.sh
source "$HERE/env.sh"

H2_PIN=1cfe254e8d25b15f37048c3730134686abe60335
OC_PIN=23fb5e0516c99ac04a1aa46c193efda2e1b9bb24
H2="$W/tmp/harness2"
OC="$H2/dependencies/opencode"
TOOLS="$H2/dependencies/tools"
BUN="$TOOLS/node_modules/.bin/bun"
PATCH="$H2/third_party/patches/opencode-compat.diff"
# Prefer the nimo 3.12.12 path. Any other cpython-3.12.x under the uv dir
# is accepted. HARNESS2_PY312 is the test stand-in (and an operator override).
pick_py312() {
  if [[ -n "${HARNESS2_PY312:-}" ]]; then
    printf '%s\n' "$HARNESS2_PY312"
    return
  fi
  local preferred="$HOME/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu/bin/python3.12"
  if [[ -e "$preferred" ]]; then
    printf '%s\n' "$preferred"
    return
  fi
  local cand
  shopt -s nullglob
  for cand in "$HOME"/.local/share/uv/python/cpython-3.12.*/bin/python3.12; do
    printf '%s\n' "$cand"
    shopt -u nullglob
    return
  done
  shopt -u nullglob
  printf '%s\n' "$preferred"
}
PY_LINK=$(pick_py312)
STATE="$W/tmp/state"

print_steps() {
  cat <<EOF
1. git clone https://github.com/google-research/harness2 ${H2} && git -C ${H2} checkout --detach ${H2_PIN}
2. UV_PYTHON_DOWNLOADS=never; PY312=\$(realpath ${PY_LINK}) && uv venv --python "\$PY312" ${H2}/.venv && uv pip install --python ${H2}/.venv/bin/python -e ${H2}
3. git init -q ${OC} && git -C ${OC} remote add origin https://github.com/anomalyco/opencode.git && git -C ${OC} fetch --depth 1 origin ${OC_PIN} && git -C ${OC} checkout --detach FETCH_HEAD && git -C ${OC} apply --check ${PATCH} && git -C ${OC} apply ${PATCH}
4. npm install --prefix ${TOOLS} bun@1.3.11
5. cd ${OC} && ${BUN} install --frozen-lockfile --ignore-scripts
6. python3 ${HERE}/check.py --root ${H2}
env: written from env.local.example
EOF
}

if [[ "${1:-}" == "--dry-run" ]]; then
  print_steps
  exit 0
fi

# Directories match env.sh. Do not expand those variables here: an unset
# npm_config_cache must still reach the stub-env test as a missing child var.
mkdir -p "$STATE" \
  "$STATE/uv-cache" "$STATE/uv-python" "$STATE/uv-bin" "$STATE/uv-tools" \
  "$STATE/npm-cache" "$STATE/bun-cache" "$STATE/bun" \
  "$STATE/xdg-config" "$STATE/xdg-cache" "$STATE/xdg-data" "$STATE/xdg-state"
export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL="$STATE/empty-gitconfig"
if [[ ! -f "$GIT_CONFIG_GLOBAL" ]]; then
  : >"$GIT_CONFIG_GLOBAL"
fi

say() { printf '%s\n' "$*" | tee -a "$STATE/stage.log"; }

python3 "$HERE/common.py" home-snapshot >"$STATE/home.base"

verify_home() {
  python3 "$HERE/common.py" home-snapshot >"$STATE/home.now" || {
    echo "BLOCKED: home-write" >&2
    echo "home snapshot failed" >&2
    exit 2
  }
  local rc=0
  python3 "$HERE/common.py" home-diff "$STATE/home.base" "$STATE/home.now" >"$STATE/home.diff" || rc=$?
  if [[ "$rc" -ne 0 ]]; then
    echo "BLOCKED: home-write" >&2
    cat "$STATE/home.diff" >&2
    exit 2
  fi
}

run_step() {
  local n="$1"
  shift
  say "step ${n}: start"
  set +e
  "$@"
  local rc=$?
  set -e
  verify_home
  if [[ "$rc" -ne 0 ]]; then
    echo "step ${n} failed rc=${rc}" >&2
    exit "$rc"
  fi
  say "step ${n}: ok"
}

step1() {
  if [[ -e "$H2/.git" ]]; then
    local cur
    cur=$(git -C "$H2" rev-parse HEAD) || return $?
    if [[ "$cur" != "$H2_PIN" ]]; then
      echo "refusing existing checkout at ${cur} (want ${H2_PIN})" >&2
      return 2
    fi
    say "step 1: checkout already at ${H2_PIN}"
    return 0
  fi
  say "run: git clone https://github.com/google-research/harness2 ${H2}"
  git clone https://github.com/google-research/harness2 "$H2" || return $?
  say "run: git -C ${H2} checkout --detach ${H2_PIN}"
  git -C "$H2" checkout --detach "$H2_PIN" || return $?
}

step2() {
  if [[ ! -e "$PY_LINK" ]]; then
    echo "BLOCKED: no-python312" >&2
    return 2
  fi
  local py
  py=$(realpath "$PY_LINK") || return $?
  if [[ ! -x "$py" ]]; then
    echo "BLOCKED: no-python312" >&2
    return 2
  fi
  local prefix="$HOME/.local/share/uv/python/"
  case "$py" in
    "$prefix"cpython-3.12.*/bin/python3.12) ;;
    *)
      echo "BLOCKED: no-python312 (not a 3.12.x uv interpreter: ${py})" >&2
      return 2
      ;;
  esac
  say "run: uv venv --python ${py} ${H2}/.venv"
  uv venv --python "$py" "$H2/.venv" || return $?
  say "run: uv pip install --python ${H2}/.venv/bin/python -e ${H2}"
  uv pip install --python "$H2/.venv/bin/python" -e "$H2" || return $?
}

step3() {
  if [[ -e "$OC/.git" ]]; then
    local cur
    cur=$(git -C "$OC" rev-parse HEAD) || return $?
    if [[ "$cur" != "$OC_PIN" ]]; then
      echo "refusing existing opencode checkout at ${cur} (want ${OC_PIN})" >&2
      return 2
    fi
    say "step 3: opencode already at ${OC_PIN}"
  else
    say "run: git init -q ${OC}"
    git init -q "$OC" || return $?
    say "run: git -C ${OC} remote add origin https://github.com/anomalyco/opencode.git"
    git -C "$OC" remote add origin https://github.com/anomalyco/opencode.git || return $?
    say "run: git -C ${OC} fetch --depth 1 origin ${OC_PIN}"
    git -C "$OC" fetch --depth 1 origin "$OC_PIN" || return $?
    say "run: git -C ${OC} checkout --detach FETCH_HEAD"
    git -C "$OC" checkout --detach FETCH_HEAD || return $?
  fi
  if git -C "$OC" apply --reverse --check "$PATCH" >/dev/null 2>&1; then
    say "opencode patch already applied"
    return 0
  fi
  say "run: git -C ${OC} apply --check ${PATCH}"
  git -C "$OC" apply --check "$PATCH" || return $?
  say "run: git -C ${OC} apply ${PATCH}"
  git -C "$OC" apply "$PATCH" || return $?
}

step4() {
  say "run: npm install --prefix ${TOOLS} bun@1.3.11"
  npm install --prefix "$TOOLS" bun@1.3.11 || return $?
}

step5() {
  say "run: ${BUN} install --frozen-lockfile --ignore-scripts"
  (cd "$OC" && "$BUN" install --frozen-lockfile --ignore-scripts) || return $?
}

write_env() {
  local dest="$H2/.env"
  if [[ -f "$dest" ]]; then
    say "env: kept existing .env"
    return 0
  fi
  sed "s#@W@#${W}#g" "$HERE/env.local.example" >"$dest"
  say "env: written from env.local.example"
}

step6() {
  write_env || return $?
  python3 "$HERE/common.py" write-opencode-config >/dev/null || return $?
  say "run: python3 ${HERE}/check.py --root ${H2}"
  python3 "$HERE/check.py" --root "$H2" || return $?
}

say "stage: W=${W} harness2=${H2_PIN} opencode=${OC_PIN}"
run_step 1 step1
run_step 2 step2
run_step 3 step3
run_step 4 step4
run_step 5 step5
run_step 6 step6
say "stage: ok"
