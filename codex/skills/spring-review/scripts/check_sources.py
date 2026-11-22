#!/usr/bin/env python3
"""Run installed standalone linters without modifying the reviewed project."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from environment import load_environment
sys.path.insert(0, str(Path(__file__).resolve().parent))
from setup_tools import cached_command

EXCLUDED = {'.git', '.gradle', '.idea', 'build', 'target', 'generated', 'node_modules'}
SUFFIXES = {'ktlint': '.kt', 'detekt': '.kt', 'pmd': '.java'}
VIOLATION_CODES = {'ktlint': 1, 'detekt': 2, 'pmd': 4}


def sources(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix in {'.kt', '.java'} else []
    return sorted(p for p in target.rglob('*') if p.is_file() and not p.is_symlink()
                  and p.suffix in {'.kt', '.java'} and not EXCLUDED.intersection(p.relative_to(target).parts))


def classify(tool: str, code: int, report: Path) -> tuple[str, int]:
    try:
        root = ET.parse(report).getroot()
    except (OSError, ET.ParseError):
        return 'error', 0
    if tool == 'pmd':
        count = sum(1 for e in root.iter() if e.tag.split('}')[-1] == 'violation')
        processing_errors = any(e.tag.split('}')[-1] in {'error', 'configerror'} for e in root.iter())
        valid = root.tag.split('}')[-1] == 'pmd'
    else:
        count = len(root.findall('.//error'))
        processing_errors = any('parse' in e.get('source', '').lower() or
                                'not a valid kotlin file' in e.get('message', '').lower()
                                for e in root.findall('.//error'))
        valid = root.tag == 'checkstyle'
    if not valid or processing_errors or code not in {0, VIOLATION_CODES[tool]} or (code != 0 and not count):
        return 'error', count
    return ('findings' if count else 'passed'), count


def run_check(tool, files, output, env, timeout, classpath):
    configured = env.get('SPRING_REVIEW_' + tool.upper(), tool)
    executable = shutil.which(str(Path(configured).expanduser()), path=env.get('PATH'))
    if not executable and 'SPRING_REVIEW_' + tool.upper() not in env:
        cached = cached_command(tool, env)
        if cached.is_file() and os.access(cached, os.X_OK):
            executable = str(cached)
    result = {'tool': tool, 'source_count': len(files), 'profile': 'tool defaults',
              'status': 'unavailable', 'findings': 0}
    if not executable:
        result['reason'] = 'Install the CLI on PATH or set SPRING_REVIEW_' + tool.upper()
        return result
    report = output / f'{tool}.xml'
    # Remove a report from a previous invocation; stale output is never evidence.
    report.unlink(missing_ok=True)
    if tool == 'ktlint':
        command = [executable, f'--reporter=checkstyle,output={report}', *map(str, files)]
        result['limitations'] = ['Formatting/style only; existing .editorconfig files may apply.']
    elif tool == 'detekt':
        command = [executable, '--input', os.pathsep.join(map(str, files)), '--report', f'xml:{report}']
        if classpath:
            command += ['--classpath', classpath]
        result['limitations'] = ['Default active rules only; not a compiler or syntax-validity check. Type-dependent rules are unverified without a compatible classpath.']
    else:
        file_list = output / 'java-files.txt'
        file_list.write_text('\n'.join(map(str, files)) + '\n')
        command = [executable, 'check', '--file-list', str(file_list), '--rulesets',
                   'rulesets/java/quickstart.xml', '--format', 'xml', '--report-file', str(report)]
        if classpath:
            command += ['--aux-classpath', classpath]
        result['limitations'] = ['Quickstart rules only; unresolved dependencies can limit type-aware analysis.']
    result['command'] = command
    try:
        version = subprocess.run([executable, '--version'], env=env, capture_output=True, text=True, timeout=15)
        result['version'] = (version.stdout or version.stderr).strip()[:500]
        # Keep tool working files outside the project as well as the report files.
        with (output / f'{tool}.log').open('w') as log:
            completed = subprocess.run(command, env=env, cwd=output, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        result['exit_code'] = completed.returncode
        result['status'], result['findings'] = classify(tool, completed.returncode, report)
    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
    except OSError as error:
        result['status'] = 'error'
        result['reason'] = str(error)
    result['report'] = str(report) if report.exists() else None
    result['log'] = str(output / f'{tool}.log')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path, help='Package directory or one .java/.kt file')
    parser.add_argument('--tool', choices=['auto', *SUFFIXES], default='auto')
    parser.add_argument('--output', type=Path, help='Report directory (default: new system temporary directory)')
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--classpath', help='Optional dependency classpath; tool/compiler versions must be compatible')
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    if not target.exists() or args.timeout < 1:
        parser.error('Target must exist and timeout must be positive')
    files = sources(target)
    output = args.output.expanduser().resolve() if args.output else Path(tempfile.mkdtemp(prefix='spring-review-'))
    if output == target or (target.is_dir() and target in output.parents):
        parser.error('Reports must be written outside the reviewed source directory')
    output.mkdir(parents=True, exist_ok=True)
    env = load_environment()
    tools = list(SUFFIXES) if args.tool == 'auto' else [args.tool]
    checks = []
    for tool in tools:
        selected = [p for p in files if p.suffix == SUFFIXES[tool]]
        if selected:
            checks.append(run_check(tool, selected, output, env, args.timeout, args.classpath))
    summary = {'target': str(target), 'source_count': len(files), 'checks': checks, 'compilation': 'not_run',
               'note': 'Default diagnostics are review candidates, not established project-rule violations. '
                       'This does not verify module architecture or runtime behavior.'}
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('Reports: ' + str(output), file=sys.stderr)
    if not checks or any(c['status'] in {'unavailable', 'error', 'timeout'} for c in checks):
        return 2
    return 1 if any(c['status'] == 'findings' for c in checks) else 0


if __name__ == '__main__':
    raise SystemExit(main())
