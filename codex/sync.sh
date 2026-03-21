#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_SOURCE="$ROOT/codex"
CODEX_HOME="$HOME/.codex"
BASE_CONFIG="$CODEX_SOURCE/config.base.toml"
TARGET_CONFIG="$CODEX_HOME/config.toml"
HOME_AGENTS_SOURCE="$CODEX_SOURCE/AGENTS.user.md"
HOME_AGENTS_TARGET="$HOME/AGENTS.md"

DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage:
  ./codex/sync.sh [--dry-run]

Options:
  --dry-run     Show what would be synced without writing files
  --help        Show this help

This script manages:
  - codex/config.base.toml -> ~/.codex/config.toml (managed keys only)
  - ~/.codex/prompts, ~/.codex/skills
  - codex/AGENTS.user.md -> ~/AGENTS.md

For Codex config:
  - keys/tables present in codex/config.base.toml overwrite home config
  - home-only keys/tables not present in base are preserved
  - home config is never imported back into the repo

It intentionally ignores ~/.omx (runtime state, logs, and sessions).
USAGE

  exit 0
}

sync_file() {
  local source_path=$1
  local target_path=$2
  local label=$3

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $label: $source_path -> $target_path"
    return
  fi

  mkdir -p "$(dirname "$target_path")"
  cp -f "$source_path" "$target_path"
}

sync_codex_config() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] codex config merge: $BASE_CONFIG -> $TARGET_CONFIG"
    return
  fi

  python3 - "$BASE_CONFIG" "$TARGET_CONFIG" <<'PY'
from __future__ import annotations

import pathlib
import re
import sys
import tomllib

base_path = pathlib.Path(sys.argv[1])
target_path = pathlib.Path(sys.argv[2])

if not base_path.is_file():
    raise SystemExit(f"Base config missing: {base_path}")

with base_path.open("rb") as fh:
    base = tomllib.load(fh)

if target_path.exists():
    with target_path.open("rb") as fh:
        target = tomllib.load(fh)
else:
    target = {}

merged = {}
for key, value in base.items():
    merged[key] = value
for key, value in target.items():
    if key not in base:
        merged[key] = value

bare_key_pattern = re.compile(r"^[A-Za-z0-9_-]+$")


def format_key(key: str) -> str:
    if bare_key_pattern.match(key):
        return key
    escaped = key.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def format_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\b", "\\b")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\f", "\\f")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def format_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return format_string(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    if value is None:
        raise TypeError("TOML does not support null values")
    raise TypeError(f"Unsupported TOML value type: {type(value)!r}")


def emit_table(lines: list[str], path: list[str], table: dict) -> None:
    scalar_items = []
    child_tables = []
    for key, value in table.items():
        if isinstance(value, dict):
            child_tables.append((key, value))
        else:
            scalar_items.append((key, value))

    should_emit_header = bool(path) and (bool(scalar_items) or not child_tables)
    if should_emit_header:
        if lines:
            lines.append("")
        lines.append("[" + ".".join(format_key(part) for part in path) + "]")

    for key, value in scalar_items:
        lines.append(f"{format_key(key)} = {format_value(value)}")

    for key, value in child_tables:
        emit_table(lines, [*path, key], value)


lines: list[str] = []
emit_table(lines, [], merged)
output = "\n".join(lines) + "\n"

target_path.parent.mkdir(parents=True, exist_ok=True)
target_path.write_text(output, encoding="utf-8")
print(f"Updated {target_path} from {base_path}")
PY
}

sync_full_dir() {
  local source_dir=$1
  local target_dir=$2
  local label=$3

  if [[ $DRY_RUN -eq 1 ]]; then
    if command -v rsync >/dev/null 2>&1; then
      rsync --delete --out-format='  %n' --dry-run -a "$source_dir" "$target_dir"
    else
      find "$source_dir" -type f -print0 | xargs -0 -I{} printf '  %s\n' "{}"
    fi
    return
  fi

  mkdir -p "$target_dir"
  if command -v rsync >/dev/null 2>&1; then
    rsync --delete -a "$source_dir" "$target_dir"
  else
    find "$source_dir" -type f -print0 | while IFS= read -r -d '' file; do
      rel="${file#${source_dir}}"
      cp -f "$file" "$target_dir/$rel"
    done
  fi
}

sync_to_home() {
  sync_full_dir "$CODEX_SOURCE/prompts/" "$CODEX_HOME/prompts/" "codex prompts"
  sync_full_dir "$CODEX_SOURCE/skills/" "$CODEX_HOME/skills/" "codex skills"
  sync_file "$HOME_AGENTS_SOURCE" "$HOME_AGENTS_TARGET" "global home AGENTS"
  sync_codex_config
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

sync_to_home
