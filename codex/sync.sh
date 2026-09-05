#!/usr/bin/env bash
set -euo pipefail

CODEX_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$CODEX_SOURCE_DIR/sync.py" "$@"
