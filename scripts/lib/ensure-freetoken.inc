# sourced by scripts/pfy when split; #110 FreeToken health wait
freetoken_health() {
  curl -sf --max-time 2 http://127.0.0.1:1919/v1/models >/dev/null 2>&1 \
    || curl -sf --max-time 2 http://127.0.0.1:1919/health >/dev/null 2>&1
}

wait_freetoken_health() {
  local i
  for i in $(seq 1 12); do
    freetoken_health && return 0
    sleep 0.5
  done
  return 1
}

ensure_freetoken() {
  local bin model
  if ! have ft && ! have freetoken; then
    echo "STUB: FreeToken not on PATH. One-liner:"
    echo "  ft serve --model \$PFY_FT_MODEL"
    return 0
  fi
  bin="$(ft_bin)"
  if freetoken_health; then
    echo "FreeToken API healthy"
    return 0
  fi
  model="$(ft_default_model)"
  if [[ -z "$model" ]]; then
    echo "note: FreeToken has no model env (set PFY_FT_MODEL, or LOCAL_CODER_MODEL / FREETOKEN_MODEL) — honest skip"
    echo "  ft serve --model \$PFY_FT_MODEL"
    return 0
  fi
  echo "starting FreeToken in background (wait for /v1/models or /health on :1919): $bin serve --model $model"
  ("$bin" serve --model "$model" >>"$STATE_DIR/freetoken.log" 2>&1 &) || true
  if wait_freetoken_health; then
    echo "FreeToken API healthy"
  else
    echo "note: FreeToken launched but API not healthy (partial) — not fake ready"
  fi
}

