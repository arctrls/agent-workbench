#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXIT_ON_FIND=1

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/check-sensitive-data.sh [--warn-only]

Options:
  --warn-only  Print findings but do not exit with non-zero status
  --help       Show this help

This script scans tracked repository files for common secret/token patterns.
USAGE
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --warn-only)
      EXIT_ON_FIND=0
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

PATTERNS=(
  "OpenAI API key|sk-[A-Za-z0-9]{20,}"
  "OpenAI org key|org-[A-Za-z0-9]{20,}"
  "GitHub token|gh[pousr]_[A-Za-z0-9_]{30,}"
  "AWS access key|AKIA[0-9A-Z]{16}"
  "AWS session token|ASIA[0-9A-Z]{16}"
  "Slack token|xox[baprs]-[0-9]{10,20}-[0-9]{10,20}-[A-Za-z0-9-]+"
  "Telegram bot token|[0-9]{6,15}:[A-Za-z0-9_-]{35,}"
  "Private key header|-----BEGIN [A-Z ]*PRIVATE KEY-----"
)

IGNORE_PATTERN='(your-bot-token|your-telegram-token|placeholder|PLACEHOLDER|dummy|sample|example|YOUR_)'

cd "$ROOT"

TOTAL=0

for entry in "${PATTERNS[@]}"; do
  IFS='|' read -r label pattern <<< "$entry"
  matches="$(git ls-files -z | xargs -0 rg -n --color=never --pcre2 --no-heading "$pattern" 2>/dev/null || true)"
  if [[ -n "$matches" ]]; then
    filtered="$(printf '%s\n' "$matches" | rg -v -E "$IGNORE_PATTERN" || true)"
    if [[ -n "$filtered" ]]; then
      echo "[Potential Secret] $label"
      printf '%s\n' "$filtered"
      echo
      ((TOTAL+=1))
    fi
  fi
done

if [[ "$TOTAL" -eq 0 ]]; then
  echo "No sensitive-key patterns found in tracked files."
  exit 0
fi

echo "Detected $TOTAL secret pattern groups."
if [[ "$EXIT_ON_FIND" -eq 1 ]]; then
  echo "If these are false positives, add explicit allowlist exclusions in the script and rerun."
  exit 1
fi
echo "WARN mode enabled; continuing despite findings."
