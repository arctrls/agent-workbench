#!/usr/bin/env bash
set -euo pipefail

original_branch="$(git branch --show-current)"
source_branch="${1:-$original_branch}"

if [[ -z "$source_branch" ]]; then
  echo "Error: could not determine source branch" >&2
  exit 1
fi

if [[ "$source_branch" == "dev" ]]; then
  echo "Error: source branch is already dev" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: tracked working tree changes must be committed or stashed first" >&2
  exit 1
fi

git fetch origin dev
git switch dev
git reset --hard origin/dev

if ! git merge --no-ff "$source_branch"; then
  echo "Merge conflict detected." >&2
  echo "Stop here and ask the user to choose:" >&2
  echo "1. Recreate origin/dev from origin/main, then merge the current branch." >&2
  echo "2. Stop." >&2
  exit 2
fi

git push origin dev

if [[ -n "$original_branch" && "$original_branch" != "dev" ]]; then
  git switch "$original_branch"
fi
