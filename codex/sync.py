#!/usr/bin/env python3
"""Sync repository-owned Codex settings while preserving app-managed state."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib


MANAGED_SECTIONS = {"features", "mcp_servers"}
BARE_KEY = re.compile(r"^[A-Za-z0-9_-]+$")


def quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")


def format_key(key: str) -> str:
    return key if BARE_KEY.fullmatch(key) else quote(key)


def format_path(path: tuple[str, ...]) -> str:
    return ".".join(format_key(part) for part in path)


def same_values(left, right) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            same_values(value, right[key]) for key, value in left.items()
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            same_values(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, float) and math.isnan(left):
        return math.isnan(right)
    return left == right


def merge_managed(target: dict, managed: dict, path=()) -> tuple[dict, list[str]]:
    merged = dict(target)
    changes = []
    for key, value in managed.items():
        key_path = (*path, key)
        if isinstance(value, dict):
            existing = target.get(key, {})
            if not isinstance(existing, dict):
                raise ValueError(f"Expected a table at {format_path(key_path)}")
            merged[key], nested_changes = merge_managed(existing, value, key_path)
            changes.extend(nested_changes)
            if key not in target and not value:
                changes.append(f"add {format_path(key_path)}")
        elif key not in target or not same_values(target[key], value):
            merged[key] = value
            action = "update" if key in target else "add"
            changes.append(f"{action} {format_path(key_path)}")
    return merged, changes


def format_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return quote(value)
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, list):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(
            f"{format_key(key)} = {format_value(item)}" for key, item in value.items()
        ) + " }"
    raise TypeError(f"Unsupported TOML value type: {type(value).__name__}")


def render_toml(config: dict) -> str:
    lines = []

    def emit_table(path: tuple[str, ...], table: dict):
        scalars = [(key, value) for key, value in table.items() if not isinstance(value, dict)]
        children = [(key, value) for key, value in table.items() if isinstance(value, dict)]
        if path and (scalars or not children):
            if lines:
                lines.append("")
            lines.append(f"[{format_path(path)}]")
        for key, value in scalars:
            lines.append(f"{format_key(key)} = {format_value(value)}")
        for key, value in children:
            emit_table((*path, key), value)

    emit_table((), config)
    output = "\n".join(lines) + "\n"
    if not same_values(tomllib.loads(output), config):
        raise ValueError("Generated TOML does not preserve configuration values")
    return output


def read_existing(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


@dataclass(frozen=True)
class ConfigPlan:
    target: Path
    original: bytes | None
    output: str | None
    changes: tuple[str, ...]

    def apply(self):
        if self.output is None:
            return
        if read_existing(self.target) != self.original:
            raise ValueError("config.toml changed during sync; rerun to merge the latest settings")
        self.target.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(self.target.stat().st_mode) if self.target.exists() else 0o600
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.target.parent,
                prefix=".config.toml.sync-", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), mode)
                stream.write(self.output)
                stream.flush()
                os.fsync(stream.fileno())
            if read_existing(self.target) != self.original:
                raise ValueError("config.toml changed during sync; rerun to merge the latest settings")
            os.replace(temporary, self.target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def plan_config(source: Path, target: Path) -> ConfigPlan:
    managed = tomllib.loads(source.read_text(encoding="utf-8"))
    unexpected = managed.keys() - MANAGED_SECTIONS
    if unexpected:
        raise ValueError("App-owned config keys are not sync targets: " + ", ".join(sorted(unexpected)))
    if any(not isinstance(value, dict) for value in managed.values()):
        raise ValueError("Managed features and mcp_servers must be TOML tables")
    original = read_existing(target)
    current = tomllib.loads(original.decode("utf-8")) if original is not None else {}
    merged, changes = merge_managed(current, managed)
    output = render_toml(merged) if changes or original is None else None
    return ConfigPlan(target, original, output, tuple(changes))


@dataclass(frozen=True)
class FileSync:
    source: Path
    target: Path
    directory: bool = False
    delete: bool = False

    def unchanged_file(self) -> bool:
        if self.directory or not self.target.is_file():
            return False
        return (
            self.source.read_bytes() == self.target.read_bytes()
            and stat.S_IMODE(self.source.stat().st_mode)
            == stat.S_IMODE(self.target.stat().st_mode)
        )

    def command(self, rsync: str, *, preview: bool) -> list[str]:
        command = [rsync, "-a", "--checksum"]
        if self.delete:
            command.append("--delete")
        if preview:
            command += ["--dry-run", "--itemize-changes", "--out-format=%i %n%L"]
        suffix = "/" if self.directory else ""
        return command + [str(self.source) + suffix, str(self.target) + suffix]


def validate_target(path: Path, root: Path, *, directory: bool):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Refusing to sync through symlinked target: {part}")
        if part == root:
            break
    if path.exists() and path.is_dir() != directory:
        raise ValueError(f"Unexpected target file type: {path}")


def file_syncs(source: Path, target: Path) -> list[FileSync]:
    operations = [
        FileSync(source / "prompts", target / "prompts", directory=True),
        FileSync(source / "AGENTS.user.md", target / "AGENTS.md"),
    ]
    skills = source / "skills"
    if not skills.is_dir():
        raise ValueError(f"Skills source directory is missing: {skills}")
    for skill in sorted(skills.iterdir()):
        if skill.name.startswith(".") or not skill.is_dir():
            continue
        if not (skill / "SKILL.md").is_file():
            raise ValueError(f"Managed skill is missing SKILL.md: {skill}")
        operations.append(FileSync(skill, target / "skills" / skill.name, directory=True, delete=True))
    for operation in operations:
        valid_source = operation.source.is_dir() if operation.directory else operation.source.is_file()
        if not valid_source:
            raise ValueError(f"Sync source is missing: {operation.source}")
        validate_target(operation.target, target, directory=operation.directory)
    return operations


def sync(source: Path, target: Path, *, dry_run: bool):
    target = target.expanduser().absolute()
    resolved_target = target.resolve()
    if (resolved_target == source or source in resolved_target.parents
            or resolved_target in source.parents):
        raise ValueError("Sync target must not overlap the codex source directory")
    validate_target(target, target, directory=True)
    validate_target(target / "config.toml", target, directory=False)
    config = plan_config(source / "config.base.toml", target / "config.toml")
    operations = file_syncs(source, target)
    rsync = shutil.which("rsync")
    if rsync is None:
        raise ValueError("rsync is required; no files were changed")

    # Complete every preview before any write, including config validation.
    previews = []
    for operation in operations:
        if operation.unchanged_file():
            continue
        result = subprocess.run(operation.command(rsync, preview=True), capture_output=True, text=True, check=True)
        if result.stdout.strip():
            previews.append((operation, result.stdout.rstrip()))
    for change in config.changes:
        print(f"config.toml: {change}")
    for operation, preview in previews:
        print(f"{operation.target.relative_to(target)}:")
        for line in preview.splitlines():
            print(f"  {line}")
    if config.output is None and not previews:
        print("No changes.")
    if dry_run:
        return

    config.apply()
    for operation, _ in previews:
        operation.target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(operation.command(rsync, preview=False), capture_output=True, text=True, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show the same change plan without writing target files")
    parser.add_argument("--target-dir", type=Path, default=Path.home() / ".codex", help="Codex target directory (default: ~/.codex)")
    args = parser.parse_args()
    try:
        sync(Path(__file__).resolve().parent, args.target_dir, dry_run=args.dry_run)
    except subprocess.CalledProcessError as error:
        print(f"Sync failed: {error.stderr.strip()}", file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError) as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
