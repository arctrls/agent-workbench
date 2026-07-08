# agent-workbench

Personal AI agent configuration workspace for Codex.

This repository is the source of truth for prompts, skills, sync scripts, and
global agent defaults used in the local environment.

## What It Contains

- `codex/`: Codex prompts, skills, base config, global `AGENTS.user.md`, and sync script
- `scripts/`: repository maintenance utilities such as secret checks
- `.githooks/`: repo-managed Git hooks for automatic Codex sync on push and pull-related flows

## Sync Model

This repository syncs Codex configuration outward to local home directories.

- `./codex/sync.sh`
  - updates `~/.codex/config.toml`
  - syncs `~/.codex/prompts` and `~/.codex/skills`
  - generates `~/AGENTS.md` from `codex/AGENTS.user.md`

Generated targets should be edited here first, then synced to the home
directory. Do not treat home-directory copies as the source of truth.

## Common Commands

```bash
# Preview Codex sync
./codex/sync.sh --dry-run

# Apply Codex sync
./codex/sync.sh

# Enable repo-managed Git hooks
git config core.hooksPath .githooks

# Scan tracked files for likely secrets
./scripts/check-sensitive-data.sh
```

## Git Hooks

When `core.hooksPath` is set to `.githooks`, Codex sync runs automatically on:

- `pre-push`
- `post-merge`
- `post-rewrite` for rebase flows

This keeps `~/.codex` and `~/AGENTS.md` aligned with the repository after
common Git operations.

## Working Principles

- Keep the repository as the single source of truth.
- Prefer small, reviewable changes.
- Validate sync behavior with `--dry-run` before risky changes.
- Do not import home-directory edits back into the repository.
