---
name: hunk-review
description: Interact with live Hunk diff review sessions from Codex. Use when the user has Hunk running, asks to review a Hunk session, navigate files/hunks in Hunk, add inline agent comments, reload Hunk contents, or use Hunk's agent integration.
---

# Hunk Review

Use the installed Hunk review skill as the source of truth so this wrapper stays current across Hunk upgrades.

## Load Installed Instructions

1. Run `hunk skill path`.
2. Read the returned `SKILL.md` completely.
3. Follow those instructions for all Hunk session work.

If `hunk skill path` fails, tell the user Hunk is not installed or not on `PATH`.

## Operating Notes

- Do not launch interactive `hunk diff`, `hunk show`, or similar TUI commands yourself unless the user explicitly asks you to open Hunk.
- Prefer `hunk session ...` commands to inspect and control an already-open Hunk window.
- If no live session exists, ask the user to start one, for example `hunk diff --watch`.
- When reviewing, start with `hunk session review --repo . --json` and request raw patches only when needed.
