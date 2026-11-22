#!/usr/bin/env bash
set -euo pipefail

CODEX_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${AGENT_WORKBENCH_PYTHON:-}" ]]; then
  exec "$AGENT_WORKBENCH_PYTHON" "$CODEX_SOURCE_DIR/sync.py" "$@"
fi
if python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
  exec python3 "$CODEX_SOURCE_DIR/sync.py" "$@"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --python 3.13 python "$CODEX_SOURCE_DIR/sync.py" "$@"
fi
echo "Python 3.11+ is required; install it or uv, or set AGENT_WORKBENCH_PYTHON." >&2
exit 1
