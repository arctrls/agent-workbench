#!/usr/bin/env python3
"""Install version-pinned review CLIs in a per-user cache, outside projects."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shlex
import sys
import tempfile
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from environment import load_environment

# Checksums: Maven Central .sha256 (ktlint/detekt), official GitHub asset digest (PMD).
TOOLS = {
    'ktlint': ('1.8.0', 'https://repo.maven.apache.org/maven2/com/pinterest/ktlint/ktlint-cli/1.8.0/ktlint-cli-1.8.0-all.jar',
               '369ad2b789f95a011f807e1fcb690ccef80bd7cd014fd139e73ae82dcc0baeab'),
    'detekt': ('1.23.8', 'https://repo.maven.apache.org/maven2/io/gitlab/arturbosch/detekt/detekt-cli/1.23.8/detekt-cli-1.23.8-all.jar',
               '3afe89a11120303c73c9bdda3d8fe558dd9070a6937d27819ddc04b275381245'),
    'pmd': ('7.20.0', 'https://github.com/pmd/pmd/releases/download/pmd_releases/7.20.0/pmd-dist-7.20.0-bin.zip',
            '1d0b62c68a48eda43ee0168f341cc7891a95652e016711562dfb5f9f3593031f'),
}


def cache_root(env):
    return Path(env.get('SPRING_REVIEW_CACHE_DIR') or
                str(Path(env.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'agent-workbench/review-tools')).expanduser().resolve()


def cached_command(tool, env):
    return cache_root(env) / f'{tool}-{TOOLS[tool][0]}' / 'bin' / tool


def install(tool, env):
    version, url, digest = TOOLS[tool]
    command = cached_command(tool, env)
    destination = command.parent.parent
    marker = destination / '.sha256'
    if command.is_file() and marker.is_file() and marker.read_text().strip() == digest:
        return command
    if destination.exists():
        raise ValueError(f'Incomplete or conflicting tool cache: {destination}')
    cache = cache_root(env)
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{tool}-', dir=cache) as tmp:
        staging = Path(tmp)
        archive = staging / ('tool.zip' if tool == 'pmd' else 'tool.jar')
        sha = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=60) as response, archive.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                sha.update(chunk); output.write(chunk)
        if sha.hexdigest() != digest:
            raise ValueError(f'Checksum mismatch for {tool}; downloaded content was not installed')
        if tool == 'pmd':
            with zipfile.ZipFile(archive) as package:
                for entry in package.infolist():
                    if Path(entry.filename).is_absolute() or '..' in Path(entry.filename).parts:
                        raise ValueError('Unsafe archive member')
                package.extractall(staging)
            archive.unlink()
            invocation = 'exec bash ' + shlex.quote(str(destination / f'pmd-bin-{version}/bin/pmd')) + ' "$@"'
        else:
            invocation = 'exec "${JAVA_HOME:+$JAVA_HOME/bin/}java" -jar ' + shlex.quote(str(destination / 'tool.jar')) + ' "$@"'
        (staging / 'bin').mkdir()
        launcher = staging / 'bin' / tool
        launcher.write_text('#!/usr/bin/env bash\nset -euo pipefail\n' + invocation + '\n')
        launcher.chmod(0o755)
        (staging / '.sha256').write_text(digest + '\n')
        # All files are ready before the versioned directory becomes visible.
        staging.rename(destination)
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tools', nargs='+', choices=list(TOOLS))
    args = parser.parse_args()
    env = load_environment()
    for tool in args.tools:
        print(install(tool, env))


if __name__ == '__main__':
    main()
