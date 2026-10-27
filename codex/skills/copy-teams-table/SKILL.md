---
name: copy-teams-table
description: Copy a small or medium table to the macOS clipboard as a real HTML table that Microsoft Teams can paste, with a plain-text fallback and clipboard verification. Use when the user asks to copy a table for Teams or reports that tabs, Markdown, or aligned text pasted as plain text. Do not use for ordinary code, SQL, or prose clipboard requests.
---

# Copy Teams Table

Copy only the requested table using the bundled script. The script writes both
`public.html` and `public.utf8-plain-text` pasteboard types and verifies that both
round-trip exactly.

## Workflow

1. Identify the final table the user wants. Preserve its headers, values, and row order.
2. Convert it to tab-separated rows. Remove Markdown pipes, separator rows, bullets,
   alignment padding, and surrounding explanation.
3. Pass the TSV on standard input to `scripts/copy_teams_table.py`.
4. Treat a nonzero exit or missing `HTML verified` status as failure. Do not replace
   it with `pbcopy`, tabs, an ASCII table, or Markdown and then claim a Teams table
   was copied.
5. Respond briefly after success.

Example:

```bash
python3 scripts/copy_teams_table.py <<'TSV'
상점	미결제 주문 유지기간
CN	1시간
COM	5시간
TSV
```

Use `--no-header` only when the user explicitly wants every row rendered as data.
The default treats the first row as table headers.

## Constraints

- This skill requires macOS and `osascript` with AppKit access.
- Pass dynamic or untrusted cell content through standard input without shell
  interpolation. The script HTML-escapes every cell.
- Keep the table within the script limits: 200 rows, 30 columns, and 128 KB of TSV.
- Do not include commentary in the copied artifact.
- If clipboard verification fails, report the failure instead of asking the user to
  test an unverified clipboard format.
