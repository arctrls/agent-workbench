---
name: html-publish
description: Create a small static HTML page or single-file web artifact, verify it locally, commit it on a feature branch, push it, and open a GitHub pull request. Use when the user asks to make an HTML page/file/site/demo/report and upload, publish, raise a PR, or "올려줘" it to a repository.
---

# HTML Publish

Create a focused static HTML artifact and publish it through the repository's
normal GitHub PR flow.

## Scope

- Prefer a single self-contained `.html` file unless the repository already has
  an established static site structure.
- Keep edits limited to the requested HTML artifact and any directly required
  local assets.
- Do not introduce dependencies or build tooling unless the user explicitly
  asks or the repository already uses them for static pages.
- Preserve repository conventions for branches, commits, PR language, and file
  placement.

## Workflow

1. Inspect the repository before editing:
   - `git status --short --branch`
   - `rg --files -g '*.html' -g '*.css' -g '*.js'`
   - relevant docs such as `README.md`, `AGENTS.md`, or deploy instructions
2. Choose the smallest reasonable target path:
   - use the user's requested path when provided
   - otherwise reuse an existing static/demo/docs directory
   - only create a new directory when no clear location exists
3. Create or update the HTML:
   - include `<!doctype html>`, `<html lang="...">`, UTF-8 charset, viewport,
     and a meaningful `<title>`
   - use semantic structure and accessible labels
   - keep CSS in the file for small standalone pages
   - avoid external CDN assets unless the repository already permits them
4. Verify locally:
   - run `scripts/html-smoke-check.py <path-to-html>` from this skill
   - open the file directly when it does not require a server
   - if scripts, module imports, routing, or asset paths require HTTP, start a
     local server such as `python3 -m http.server` from the containing directory
5. If the work is visual, inspect with browser tooling or screenshots before
   claiming completion. Check desktop and mobile widths when layout matters.
6. Commit and publish:
   - create or stay on an appropriate `feature/...` branch
   - stage only the intended files
   - commit with a concise intent-focused message
   - push the branch
   - use the repository's PR workflow or `$pull-request` when available

## Publishing Rules

- Never push unrelated local changes.
- If the working tree is mixed, stop and ask which files belong in scope.
- Prefer draft PRs when the repository or user does not specify readiness.
- Include the HTML path, purpose, and validation command in the PR body.
- If GitHub CLI or authentication is missing, stop with the exact blocker.

## Command

Run the bundled smoke check after editing:

```bash
~/.codex/skills/html-publish/scripts/html-smoke-check.py path/to/page.html
```

When using the source checkout of this skill before sync, run:

```bash
codex/skills/html-publish/scripts/html-smoke-check.py path/to/page.html
```
