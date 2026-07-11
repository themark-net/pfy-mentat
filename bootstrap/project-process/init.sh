#!/usr/bin/env bash
# init.sh — Scaffold DESIGN / ADR / TODO / OQ / AGENTS into a target project.
#
# Usage:
#   ./bootstrap/project-process/init.sh /path/to/project
#   ./bootstrap/project-process/init.sh . --name my-app --vision "..."
#   ./bootstrap/project-process/init.sh ~/work/foo --force --dry-run
#   ./bootstrap/project-process/init.sh --install-skills
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="$SCRIPT_DIR/templates"
SKILL_SRC="$SCRIPT_DIR/skills"
GROK_HOME="${GROK_HOME:-$HOME/.grok}"
GROK_SKILLS_DIR="${GROK_SKILLS_DIR:-$GROK_HOME/skills}"
GROK_CLI_SKILLS=""
if [[ -d "$SCRIPT_DIR/../grok-cli/skills" ]]; then
  GROK_CLI_SKILLS="$(cd "$SCRIPT_DIR/../grok-cli/skills" && pwd)"
fi

TARGET=""
NAME="${PROJECT_NAME:-}"
FORCE=0
DRY_RUN=0
INSTALL_SKILLS=0
VISION="${VISION:-}"

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'warn: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \?//'
  cat <<'EOF'

Options:
  --name NAME          Project name (default: basename of target)
  --vision TEXT        One-line vision for DESIGN/ARCHITECTURE
  --force              Overwrite existing scaffolded files
  --dry-run            Print actions only
  --install-skills     Install process skills into ~/.grok/skills
  -h, --help           Help
EOF
  exit 0
}

install_skills() {
  log "Installing process skills → $GROK_SKILLS_DIR"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "dry-run: would install project-process (+ adr/docs/open-questions if available)"
    return 0
  fi
  mkdir -p "$GROK_SKILLS_DIR"
  local src dest name
  for src in "$SKILL_SRC"/*/; do
    [[ -d "$src" ]] || continue
    name="$(basename "$src")"
    dest="$GROK_SKILLS_DIR/$name"
    mkdir -p "$dest"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete "$src" "$dest/"
    else
      rm -rf "$dest"; mkdir -p "$dest"; cp -a "$src"/. "$dest/"
    fi
    log "  skill: $name"
  done
  if [[ -n "$GROK_CLI_SKILLS" ]]; then
    for name in adr docs open-questions; do
      if [[ -d "$GROK_CLI_SKILLS/$name" ]]; then
        dest="$GROK_SKILLS_DIR/$name"
        mkdir -p "$dest"
        if command -v rsync >/dev/null 2>&1; then
          rsync -a --delete "$GROK_CLI_SKILLS/$name/" "$dest/"
        else
          rm -rf "$dest"; mkdir -p "$dest"; cp -a "$GROK_CLI_SKILLS/$name"/. "$dest/"
        fi
        log "  skill: $name (from grok-cli)"
      fi
    done
  else
    warn "grok-cli skills not found; run bootstrap/grok-cli/install.sh for full set"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --vision) VISION="${2:-}"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --install-skills) INSTALL_SKILLS=1; shift ;;
    -*) die "unknown flag: $1" ;;
    *)
      [[ -z "$TARGET" ]] || die "unexpected argument: $1"
      TARGET="$1"
      shift
      ;;
  esac
done

[[ -d "$TEMPLATES" ]] || die "templates missing: $TEMPLATES"

if [[ "$INSTALL_SKILLS" -eq 1 && -z "$TARGET" ]]; then
  install_skills
  log "Done (skills only)."
  exit 0
fi

[[ -n "$TARGET" ]] || die "target directory required (see --help)"
[[ -d "$TARGET" ]] || die "target is not a directory: $TARGET"
TARGET="$(cd "$TARGET" && pwd)"
NAME="${NAME:-$(basename "$TARGET")}"
DATE="$(date -u +%Y-%m-%d)"
VISION="${VISION:-One-line vision for ${NAME} (edit in docs/DESIGN.md).}"

render() {
  local src="$1" dest="$2"
  if [[ -e "$dest" && "$FORCE" -ne 1 ]]; then
    log "skip (exists): ${dest#"$TARGET"/}"
    return 0
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "dry-run: write ${dest#"$TARGET"/}"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  python3 - "$src" "$dest" "$NAME" "$DATE" "$VISION" <<'PY'
import sys
from pathlib import Path
src, dest, name, date, vision = sys.argv[1:6]
text = Path(src).read_text(encoding="utf-8")
repl = {
    "{{PROJECT_NAME}}": name,
    "{{DATE}}": date,
    "{{VISION_ONE_LINER}}": vision,
    "{{GOAL_1}}": "Primary product goal (edit me)",
    "{{GOAL_2}}": "Reliability / quality goal (edit me)",
    "{{GOAL_3}}": "Operator / agent process goal (edit me)",
    "{{NON_GOAL_1}}": "Out of scope item (edit me)",
    "{{NON_GOAL_2}}": "Out of scope item (edit me)",
    "{{SYSTEM_DIAGRAM_OR_LAYERS}}": "[edit: high-level boxes]",
    "{{DATA_FLOW}}": "[edit: inputs -> core -> outputs]",
}
for k, v in repl.items():
    text = text.replace(k, v)
Path(dest).write_text(text, encoding="utf-8")
PY
  log "wrote ${dest#"$TARGET"/}"
}

log "project-process scaffold"
log "target: $TARGET"
log "name:   $NAME"
log "date:   $DATE"

while IFS= read -r -d '' src; do
  rel="${src#"$TEMPLATES"/}"
  dest="$TARGET/$rel"
  if [[ "$(basename "$src")" == ".gitkeep" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "dry-run: ensure dir $(dirname "$rel")"
    else
      mkdir -p "$(dirname "$dest")"
      [[ -e "$dest" && "$FORCE" -ne 1 ]] || : > "$dest"
    fi
    continue
  fi
  render "$src" "$dest"
done < <(find "$TEMPLATES" -type f -print0 | sort -z)

if [[ "$INSTALL_SKILLS" -eq 1 ]]; then
  install_skills
fi

cat <<EOF

Scaffold complete for: $NAME

Next:
  1. Edit docs/DESIGN.md (vision, goals, non-goals, diagram).
  2. Replace example OQ-0001 with real unknowns.
  3. As choices land, add docs/adr/0002-*.md via /adr.
  4. Drive work from docs/TODO.md.

Install agent skills (if needed):
  $0 --install-skills
  $(dirname "$SCRIPT_DIR")/grok-cli/install.sh

EOF
