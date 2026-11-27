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

from environment import load_environment


MANAGED_SECTIONS = {"features", "mcp_servers", "tui"}
# Explicit removals of retired repository-owned servers; keep other local servers.
RETIRED_MCP_SERVERS = {"atlassian", "playwright"}
# Explicit removals of retired repository-owned feature flags.
RETIRED_FEATURES = {"multi_agent"}
# Skills that only make sense inside Codex (e.g. they read Codex history); not linked for Claude Code.
CODEX_ONLY_SKILLS = frozenset({"find-session"})
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


def plan_config(source: Path, target: Path, *, environment: dict[str, str] | None = None) -> ConfigPlan:
    managed = tomllib.loads(source.read_text(encoding="utf-8"))
    unexpected = managed.keys() - MANAGED_SECTIONS
    if unexpected:
        raise ValueError("App-owned config keys are not sync targets: " + ", ".join(sorted(unexpected)))
    if any(not isinstance(value, dict) for value in managed.values()):
        raise ValueError("Managed features, mcp_servers, and tui must be TOML tables")
    env = environment or {}
    required = ("MYSQL_READ_DEV_HOST", "MYSQL_READ_DEV_SECRET_ARN", "MYSQL_READ_DEV_DATABASE", "MYSQL_READ_DEV_REGION")
    supplied = [key for key in required if env.get(key)]
    if supplied and len(supplied) != len(required):
        raise ValueError("Missing environment settings: " + ", ".join(key for key in required if not env.get(key)))
    if supplied:
        managed.setdefault("mcp_servers", {})["mysql-mcp-server"] = {
            "command": "uvx",
            "args": ["--with", "mcp<2", "awslabs.mysql-mcp-server==1.0.20",
                     "--hostname", env[required[0]], "--secret_arn", env[required[1]],
                     "--database", env[required[2]], "--region", env[required[3]], "--readonly", "True"],
            "env": {"AWS_PROFILE": env.get("MYSQL_READ_DEV_PROFILE", "default"),
                    "AWS_REGION": env[required[3]], "FASTMCP_LOG_LEVEL": "ERROR"},
        }
    rea = managed.get("mcp_servers", {}).get("rea")
    if rea is not None:
        rea["command"] = str(Path(env["REA_NPX"]).expanduser()) if env.get("REA_NPX") else "npx"
        if env.get("REA_NODE_PATH"):
            rea["env"] = {"PATH": str(Path(env["REA_NODE_PATH"]).expanduser()) + os.pathsep + env.get("PATH", os.defpath)}
    original = read_existing(target)
    current = tomllib.loads(original.decode("utf-8")) if original is not None else {}
    if rea is not None and "REA_NPX" not in env:
        # A fresh checkout must not discard an existing machine's working runtime override.
        existing_rea = current.get("mcp_servers", {}).get("rea", {})
        if existing_rea.get("command"):
            rea["command"] = existing_rea["command"]
    merged, changes = merge_managed(current, managed)
    if rea is not None and "REA_NODE_PATH" in env and not env["REA_NODE_PATH"]:
        rea_env = merged["mcp_servers"]["rea"].get("env", {})
        if "PATH" in rea_env:
            del rea_env["PATH"]
            changes.append("remove mcp_servers.rea.env.PATH")
    features = merged.get("features", {})
    retired_features = features.keys() & RETIRED_FEATURES
    if retired_features:
        merged["features"] = {
            name: value for name, value in features.items() if name not in retired_features
        }
        changes.extend(f"remove features.{name}" for name in sorted(retired_features))
    servers = merged.get("mcp_servers", {})
    retired = servers.keys() & RETIRED_MCP_SERVERS
    if retired:
        merged["mcp_servers"] = {
            name: settings for name, settings in servers.items() if name not in retired
        }
        changes.extend(f"remove mcp_servers.{name}" for name in sorted(retired))
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
    for helper in ("environment.py", "with-env.py"):
        if (source / helper).is_file():
            operations.append(FileSync(source / helper, target / helper))
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


def plan_skill_links(directory: Path, label: str, operations: list[FileSync], source: Path, target: Path,
                     *, exclude: frozenset[str] = frozenset()) -> list[tuple[str, Path, Path]]:
    """Plan per-skill links into a discovery directory, refusing entries owned by others."""
    directory = directory.expanduser().absolute()
    validate_target(directory, directory, directory=True)
    if directory.resolve() == (target / "skills").resolve():
        raise ValueError(f"{label} directory must differ from installed skills directory")
    links = []
    for operation in operations:
        if operation.source.parent != source / "skills" or operation.source.name in exclude:
            continue
        link = directory / operation.source.name
        destination = operation.target.resolve()
        if link.is_symlink() and link.resolve() == destination:
            continue
        if link.exists() or link.is_symlink():
            raise ValueError(f"{label} already exists with a different owner: {link}")
        links.append((label, link, destination))
    return links


def sync(source: Path, target: Path, *, dry_run: bool, environment=None, shared_skills: Path | None = None,
         claude_skills: Path | None = None):
    target = target.expanduser().absolute()
    resolved_target = target.resolve()
    if (resolved_target == source or source in resolved_target.parents
            or resolved_target in source.parents):
        raise ValueError("Sync target must not overlap the codex source directory")
    validate_target(target, target, directory=True)
    validate_target(target / "config.toml", target, directory=False)
    config = plan_config(source / "config.base.toml", target / "config.toml", environment=environment)
    operations = file_syncs(source, target)
    links = []
    if shared_skills is not None:
        links += plan_skill_links(shared_skills, "shared skills", operations, source, target)
    if claude_skills is not None:
        links += plan_skill_links(claude_skills, "claude skills", operations, source, target,
                                  exclude=CODEX_ONLY_SKILLS)
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
    for label, link, _ in links:
        print(f"{label}: link {link.name}")
    if config.output is None and not previews and not links:
        print("No changes.")
    if dry_run:
        return

    config.apply()
    for operation, _ in previews:
        operation.target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(operation.command(rsync, preview=False), capture_output=True, text=True, check=True)
    for _, link, destination in links:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(destination, target_is_directory=True)


def content_target(target: Path) -> Path:
    """Follow an existing account's deliberate content sharing, never its auth."""
    target = target.expanduser().absolute()
    config = target / "config.toml"
    if not config.is_symlink():
        return target
    shared = config.resolve().parent
    if config.resolve().name != "config.toml" or shared == target:
        raise ValueError("Invalid shared config target")
    for name in ("AGENTS.md", "skills", "prompts"):
        entry = target / name
        if not entry.is_symlink() or entry.resolve() != (shared / name).resolve():
            raise ValueError("Account has partially shared content; select its canonical --target-dir explicitly")
    return shared


def default_target() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show the same change plan without writing target files")
    parser.add_argument("--target-dir", type=Path, help="Codex target directory (default: CODEX_HOME or ~/.codex)")
    parser.add_argument("--shared-skills-dir", type=Path, help="Publish owned skill links here (normally ~/.agents/skills)")
    parser.add_argument("--claude-skills-dir", type=Path, help="Publish owned skill links for Claude Code (normally ~/.claude/skills)")
    args = parser.parse_args()
    try:
        # An explicit target is isolated unless its discovery directories are also explicit.
        shared = args.shared_skills_dir
        claude = args.claude_skills_dir
        if args.target_dir is None:
            shared = shared or Path.home() / ".agents/skills"
            claude = claude or Path.home() / ".claude/skills"
        sync(Path(__file__).resolve().parent, args.target_dir or content_target(default_target()),
             dry_run=args.dry_run, environment=load_environment(), shared_skills=shared, claude_skills=claude)
    except subprocess.CalledProcessError as error:
        print(f"Sync failed: {error.stderr.strip()}", file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError) as error:
        print(f"Sync failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
