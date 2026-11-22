#!/usr/bin/env python3
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from environment import load_environment

if not 2 <= len(sys.argv) <= 3:
    raise SystemExit('Usage: open-file.py FILE[:LINE] [LINE]')
env = load_environment()
command = str(Path(env.get('VOPEN_COMMAND', 'vopen')).expanduser())
if not shutil.which(command, path=env.get('PATH')):
    raise SystemExit('Editor command unavailable; install vopen or set VOPEN_COMMAND to its executable path.')
result = subprocess.run([command, *sys.argv[1:]], env=env)
if result.returncode:
    print("If the editor reports a missing server, start " + env.get('VLISTEN_COMMAND', 'vlisten') +
          " in the desired workspace. No server was started automatically.", file=sys.stderr)
raise SystemExit(result.returncode)
