#!/usr/bin/env bash
# Shared helpers: detect Ollama models for soft-optional / hard-when-present voice evals.
# Source from other scripts:  source "$(dirname "$0")/lib-local-model.sh"
# shellcheck shell=bash

# Print matched model tag to stdout; empty if none. Exit 0 always.
# Prefers LOCAL_TOOLS_MODEL, then LOCAL_CODER_MODEL, then any deepseek-coder tag.
pfy_detect_local_model() {
  if ! command -v ollama >/dev/null 2>&1; then
    return 0
  fi
  local list match=""
  list="$(ollama list 2>/dev/null || true)"
  [[ -z "$list" ]] && return 0

  if [[ -n "${LOCAL_TOOLS_MODEL:-}" ]] && printf '%s\n' "$list" | grep -qF "${LOCAL_TOOLS_MODEL%%:*}"; then
    match="$LOCAL_TOOLS_MODEL"
  elif [[ -n "${LOCAL_CODER_MODEL:-}" ]] && printf '%s\n' "$list" | grep -qF "${LOCAL_CODER_MODEL%%:*}"; then
    match="$LOCAL_CODER_MODEL"
  elif printf '%s\n' "$list" | grep -qi 'deepseek-coder'; then
    match="$(printf '%s\n' "$list" | grep -i 'deepseek-coder' | head -1 | awk '{print $1}')"
  elif printf '%s\n' "$list" | grep -qiE 'qwen2\.5-coder|qwen3-coder|coder'; then
    match="$(printf '%s\n' "$list" | grep -iE 'qwen2\.5-coder|qwen3-coder|coder' | head -1 | awk '{print $1}')"
  fi
  printf '%s' "$match"
}

# Write a SKIP/PASS receipt under OUT for CI artifacts.
# Args: out_dir task_id kind(skip|pass|fail) reason [extra_lines...]
pfy_write_eval_receipt() {
  local out="$1" task="$2" kind="$3" reason="$4"
  shift 4 || true
  mkdir -p "$out"
  local f="$out/local-eval-${task}-${kind}.md"
  {
    echo "# voice local eval — ${task} ${kind}"
    echo "- When: $(date -Iseconds 2>/dev/null || date)"
    echo "- Task: $task"
    echo "- Kind: $kind"
    echo "- Reason: $reason"
    for line in "$@"; do
      echo "- $line"
    done
  } >"$f"
  echo "  wrote $f"
}
