---
name: pull-request
description: "Draft an intent-focused pull request, confirm it with the user, push the current branch when needed, and create a GitHub PR against `main`. The skill instructions are written in English and should explicitly account for Korean-user collaboration context."
---

# GitHub Pull Request Automation

Analyze the current branch, draft an intent-focused pull request, confirm the
draft with the user, and create the PR with GitHub CLI.

This skill may be used in repositories with Korean users. Keep that context in
mind when choosing the PR body language and phrasing, but follow the
repository's dominant documentation language first.

## Workflow

1. Confirm the current directory is inside a Git repository.
2. Read the current branch name.
3. Require the branch to start with `feature/`, `bugfix/`, or `refactor/`.
4. Check `git status --porcelain`. If anything is uncommitted, stop and tell
   the user to commit first.
5. Confirm the `origin` remote exists.
6. Confirm `gh` is installed and authenticated.
7. Run `git fetch origin main`. If it fails, stop and report the failure.
8. Check whether the current branch already has an open PR. If it does, stop,
   show the existing PR URL, and do not create another one.
9. Read the diff and commit range against `origin/main`. If there is no
   meaningful change, stop and say there is nothing to open a PR for.
10. Use the diff and conversation context to infer the PR intent.
11. Draft the PR title and body using the rules below.
12. Show the draft to the user and ask for approval before creating anything.
13. If the user requests edits, revise the draft and ask again.
14. Before creating the PR:
    - if the branch has no upstream on `origin`, run `git push -u origin HEAD`
    - if the branch already exists on `origin` but local HEAD is ahead, run
      `git push`
15. Run `gh pr create --base main --title ... --body ...`.
16. Return the PR URL and the exact title and body that were used.

## Title Rules

- Always use this format: `{{branch_name}} | {{title}}`
- `branch_name` must be the current Git branch name exactly as-is
- Do not rewrite, shorten, or interpret the branch prefix
- Use the allowed prefixes only as validation, not as a writing input
- `title` must be short, clear, and focused on intent
- Prefer why the PR exists over a list of implementation details

## Body Rules

- Write the body as concise bullet points only
- Keep it short, usually 2-4 bullets
- Emphasize intent, motivation, expected effect, or risk reduction
- Do not turn the body into a file list, diff summary, or commit log
- Keep implementation details secondary unless they are necessary for context

## Language Rules

- Prefer the repository's dominant documentation language
- Determine that language from repository-facing docs and instruction files
- If the dominant language is unclear, default to Korean
- If the user explicitly requests a specific language, follow that request

## Required Checks

- Git repository exists
- Branch prefix is one of `feature/`, `bugfix/`, `refactor/`
- Working tree is clean
- `origin` remote exists
- GitHub CLI is available and authenticated
- `git fetch origin main` succeeds
- No open PR already exists for the current branch
- The branch has meaningful changes relative to `origin/main`
- The user has approved the final draft

## Notes

- Base branch is always `main`
- Never create the PR before showing the draft to the user
- Stop immediately when a required check fails
- When reporting a failure, be specific about the blocking condition
