---
name: vopen
description: Open a local file in the already-running Neovim instance through the user's `vopen` command. Use when the user invokes `$vopen` with a file path or `file:line` target, asks to show a file in the open Vim/Neovim session, or says Korean phrases like "에디터로 열어", "vim으로 열어", "neovim으로 열어", "vim에서 보여줘", "열린 vim에 띄워줘", or "편집기로 열어".
---

# Vopen

Open the requested file in the user's already-running Neovim session by calling the local `vopen` command.

## Trigger Phrases

Use this skill for requests such as:

- `$vopen AGENTS.md`
- `AGENTS.md 에디터로 열어`
- `README.md vim으로 열어`
- `codex/skills/vopen/SKILL.md neovim에서 보여줘`
- `이 파일 열린 vim에 띄워줘`
- `편집기로 열어줘`

## Workflow

1. Resolve the target file path from the user's request.
   Preserve `file:line` targets when provided.
2. Run `vopen <file>` or `vopen <file> <line>` from the relevant workspace.
3. If `vopen` reports that the remote socket is missing, tell the user to start Neovim with `vlisten .` in the desired workspace.
4. Keep the response brief after a successful open.

## Command Forms

```bash
vopen path/to/file
vopen path/to/file 42
vopen path/to/file:42
```

## Guardrails

- Do not edit the file unless the user also asks for edits.
- Do not start `vlisten` automatically unless the user explicitly asks.
- Prefer the repository-relative path when the target is in the current workspace.
