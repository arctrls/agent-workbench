"""Read optional per-user settings as literal KEY=value data, never shell code."""
from __future__ import annotations

import os
from pathlib import Path
import re


def environment_file(environ: dict[str, str]) -> Path:
    return Path(environ.get('AGENT_WORKBENCH_ENV_FILE') or
                str(Path(environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'agent-workbench/env')).expanduser()


def load_environment(environ: dict[str, str] | None = None) -> dict[str, str]:
    process = dict(os.environ if environ is None else environ)
    path = environment_file(process)
    values = {}
    if path.exists():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            key, sep, value = line.partition('=')
            if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
                raise ValueError(f'Invalid environment entry at {path}:{number}; expected KEY=value')
            values[key] = value  # no quotes, expansion, command substitution, or inline comments
    values.update(process)
    return values
