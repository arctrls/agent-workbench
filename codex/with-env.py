#!/usr/bin/env python3
"""Run a workbench helper with literal per-user settings and inherited credentials."""
import os
import sys
from environment import load_environment

if len(sys.argv) < 2:
    raise SystemExit('Usage: with-env.py COMMAND [ARGS...]')
try:
    env = load_environment()
    env['AGENT_WORKBENCH_ENV_LOADED'] = '1'
    os.execvpe(sys.argv[1], sys.argv[1:], env)
except (ValueError, OSError) as error:
    raise SystemExit(str(error))
