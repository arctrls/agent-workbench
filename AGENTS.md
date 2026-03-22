# Repository Guidelines

## Project Structure & Module Organization

This repository is the source of truth for personal Codex tooling configuration. Keep edits here first, then sync to home directories.

- `codex/`: Codex prompts, skills, `config.base.toml`, `AGENTS.user.md`, and `sync.sh`
- `scripts/`: repository maintenance utilities such as secret checks

Do not edit generated files in `~/.codex` or `~/AGENTS.md` directly.

## Build, Test, and Development Commands

This repo has no app build pipeline. The main workflow is validation plus sync:

- `./codex/sync.sh`: sync `codex/` into home config and generate `~/AGENTS.md`
- `./codex/sync.sh --dry-run`: preview Codex sync changes
- `git config core.hooksPath .githooks`: enable repo-managed Git hooks for Codex sync on push/pull
- `./scripts/check-sensitive-data.sh`: scan tracked files for likely secrets before commit
- `./scripts/check-sensitive-data.sh --warn-only`: report findings without failing

## Coding Style & Naming Conventions

Use Markdown for prompts and guides, TOML for Codex config, and Bash for repo automation.

- Prefer concise, task-focused Markdown with stable headings
- Name skills as lowercase hyphenated directories with `SKILL.md` inside, for example `codex/skills/commit/SKILL.md`
- Keep every skill name limited to lowercase letters, numbers, and hyphens only; set the `SKILL.md` frontmatter `name` to match the parent directory name exactly, and do not use namespace-style separators such as `:`
- Keep shell scripts POSIX-friendly where practical and start with `set -euo pipefail`
- Preserve existing directory conventions instead of inventing new top-level folders

## Testing Guidelines

There is no formal test suite yet. Validate changes by running the relevant sync script in `--dry-run` mode and, for script changes, executing the real command in a safe environment.

When editing detection or sync logic:

- verify both normal and `--dry-run` behavior
- confirm paths and deletions carefully before syncing
- run `./scripts/check-sensitive-data.sh` before opening a PR

## Commit & Pull Request Guidelines

Recent history favors short conventional messages such as `chore(config): ...`, `fix(codex): ...`, and `refactor(sync): ...`. Follow that style and keep each commit scoped to one concern.

Pull requests should include:

- a short description of what changed and why
- affected paths, such as `codex/` or `scripts/`
- notes on validation commands you ran
- screenshots only when UI-facing docs or images changed

## Security & Sync Rules

This repository is the canonical configuration source. Sync from the repo to home directories only; never import home-directory changes back into the repo.
