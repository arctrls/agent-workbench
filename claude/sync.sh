#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="$HOME/.claude"
SUPERPOWERS_BASE="$CLAUDE_HOME/plugins/cache/superpowers-marketplace/superpowers"

DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage:
  ./claude/sync.sh [--dry-run]

Options:
  --dry-run     Show what would be synced without writing files
  --help        Show this help

This script syncs the repository Claude assets into ~/.claude using
non-destructive copy semantics, then refreshes the superpowers skills symlink
if the plugin cache exists.
USAGE
  exit 0
}

copy_file() {
  local source_path=$1
  local target_path=$2
  local label=$3

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $label: ${source_path} -> ${target_path}"
    return
  fi

  mkdir -p "$(dirname "$target_path")"
  cp -f "$source_path" "$target_path"
}

sync_dir() {
  local source_dir=$1
  local target_dir=$2
  local label=$3

  if [[ $DRY_RUN -eq 1 ]]; then
    if command -v rsync >/dev/null 2>&1; then
      rsync --out-format='  %n' --dry-run -a "$source_dir/" "$target_dir/"
    else
      find "$source_dir" -type f -print0 | xargs -0 -I{} printf '[dry-run] %s: %s -> %s\n' "$label" "{}" "$target_dir"
    fi
    return
  fi

  mkdir -p "$target_dir"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a "$source_dir/" "$target_dir/"
  else
    cp -R "$source_dir/." "$target_dir/"
  fi
}

link_superpowers() {
  if [[ ! -d "$SUPERPOWERS_BASE" ]]; then
    echo "[skip] superpowers: plugin cache missing: ${SUPERPOWERS_BASE}"
    return
  fi

  local latest_ver
  latest_ver="$(ls -1 "$SUPERPOWERS_BASE" | sort -V | tail -1)"
  if [[ -z "$latest_ver" ]]; then
    echo "[skip] superpowers: no plugin versions found in ${SUPERPOWERS_BASE}"
    return
  fi

  local target="$CLAUDE_HOME/skills/superpowers"
  local source="$SUPERPOWERS_BASE/$latest_ver/skills"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] superpowers: ${source} -> ${target}"
    return
  fi

  mkdir -p "$(dirname "$target")"
  rm -f "$target"
  ln -s "$source" "$target"
  echo "Linked superpowers skills (v$latest_ver)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
  shift
done

copy_file "$ROOT/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md" "claude root doc"
sync_dir "$ROOT/claude/commands" "$CLAUDE_HOME/commands" "claude commands"
sync_dir "$ROOT/claude/agents" "$CLAUDE_HOME/agents" "claude agents"
sync_dir "$ROOT/claude/docs" "$CLAUDE_HOME/docs" "claude docs"
sync_dir "$ROOT/claude/skills" "$CLAUDE_HOME/skills" "claude skills"
sync_dir "$ROOT/claude/obsidian-presets" "$CLAUDE_HOME/obsidian-presets" "claude obsidian presets"
copy_file "$ROOT/claude/settings.json" "$CLAUDE_HOME/settings.json" "claude settings"
copy_file "$ROOT/claude/claude-powerline.json" "$CLAUDE_HOME/claude-powerline.json" "claude powerline"
link_superpowers
