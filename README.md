# agent-workbench

Personal AI agent configuration workspace for Codex.

This repository is the source of truth for prompts, skills, sync scripts, and
global agent defaults used in the local environment.

## What It Contains

- `codex/`: Codex prompts, skills, managed config, global `AGENTS.user.md`, and sync scripts
- `scripts/`: repository maintenance utilities such as secret checks
- `.githooks/`: repo-managed Git hooks for automatic Codex sync on push and pull-related flows

## Sync Model

This repository syncs only repository-owned configuration outward to local home
directories. It requires Python 3.11+ and `rsync`; no Python packages are needed.

- `./codex/sync.sh`
  - recursively merges only `[features]` and `[mcp_servers]` keys from
    `codex/config.base.toml` into `~/.codex/config.toml`
  - preserves model/reasoning preferences, plugin state, and all other local keys
  - updates prompts without deleting local-only prompt files
  - syncs each repository-owned skill separately, deleting stale files only
    inside that skill's directory
  - preserves `.system` and skills installed outside this repository
  - generates `~/.codex/AGENTS.md` from `codex/AGENTS.user.md`

Edit repository-owned items here first. The app owns its runtime settings and
built-in skills; existing `codex/skills/.system` snapshots are not deployed.
Removing a skill or config key from the repository does not delete it from the
home directory. Such removals must be handled explicitly.

`sync.sh` remains the entry point; `sync.py` prepares and validates the complete
change plan before writing. Dry-run shows that same plan, including deletions,
without printing config values. Changed config is re-parsed and atomically
replaced; unchanged config is left byte-for-byte intact. When config values do
change, TOML formatting and comments are regenerated rather than preserved.
Managed destination symlinks are rejected to avoid writing outside their scope.

Config changes detected during preparation or staging abort the sync. The app
does not share a lock with this script, so a concurrent write in the final
check/replace interval remains possible. Config replacement is atomic, but the
entire multi-file sync is not a transaction: an I/O failure during rsync can leave
some repository-owned files updated. Review the error and rerun after fixing it.

## Common Commands

```bash
# Preview Codex sync
./codex/sync.sh --dry-run

# Apply Codex sync
./codex/sync.sh

# Use an isolated target without changing HOME
./codex/sync.sh --target-dir /tmp/codex-sync-check --dry-run

# Run sync regression tests (temporary directories only)
python3 -m unittest discover -s scripts/tests -p 'test_codex_sync.py' -v

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

This updates repository-owned items after common Git operations while retaining
app-managed settings and skills.

## Working Principles

- Keep the repository as the single source of truth.
- Prefer small, reviewable changes.
- Validate sync behavior with `--dry-run` before risky changes.
- Do not import home-directory edits back into the repository.
