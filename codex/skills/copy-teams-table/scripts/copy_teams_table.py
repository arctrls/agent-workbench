#!/usr/bin/env python3
"""Copy tab-separated input as a real HTML table for Microsoft Teams."""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import subprocess
import sys
from collections.abc import Sequence


MAX_INPUT_BYTES = 128_000
MAX_ROWS = 200
MAX_COLUMNS = 30


class TableInputError(ValueError):
    """The supplied tabular input cannot be copied safely."""


def parse_tsv(value: str) -> list[list[str]]:
    if len(value.encode("utf-8")) > MAX_INPUT_BYTES:
        raise TableInputError(f"input exceeds {MAX_INPUT_BYTES} bytes")

    rows = list(csv.reader(io.StringIO(value), delimiter="\t"))
    while rows and (not rows[-1] or all(cell == "" for cell in rows[-1])):
        rows.pop()
    if not rows:
        raise TableInputError("table input is empty")
    if len(rows) > MAX_ROWS:
        raise TableInputError(f"table exceeds {MAX_ROWS} rows")

    column_count = len(rows[0])
    if column_count == 0:
        raise TableInputError("table has no columns")
    if column_count > MAX_COLUMNS:
        raise TableInputError(f"table exceeds {MAX_COLUMNS} columns")

    for position, row in enumerate(rows, start=1):
        if len(row) != column_count:
            raise TableInputError(
                f"row {position} has {len(row)} columns; expected {column_count}"
            )
    return rows


def _cell(value: str) -> str:
    return html.escape(value, quote=True).replace("\n", "<br>")


def render_html(rows: Sequence[Sequence[str]], *, has_header: bool) -> str:
    table_style = (
        "border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px"
    )
    header_style = (
        "border:1px solid #8a8a8a;padding:6px 10px;text-align:left;"
        "background:#f2f2f2;font-weight:600"
    )
    cell_style = "border:1px solid #8a8a8a;padding:6px 10px;text-align:left"

    parts = [f'<meta charset="utf-8"><table style="{table_style}">']
    body_start = 0
    if has_header:
        parts.append("<thead><tr>")
        parts.extend(
            f'<th scope="col" style="{header_style}">{_cell(value)}</th>'
            for value in rows[0]
        )
        parts.append("</tr></thead>")
        body_start = 1

    parts.append("<tbody>")
    for row in rows[body_start:]:
        parts.append("<tr>")
        parts.extend(
            f'<td style="{cell_style}">{_cell(value)}</td>' for value in row
        )
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def render_plain(rows: Sequence[Sequence[str]]) -> str:
    return "\n".join("\t".join(row) for row in rows)


def copy_to_macos_clipboard(html_table: str, plain_text: str) -> None:
    if sys.platform != "darwin":
        raise RuntimeError("copy-teams-table currently requires macOS")

    jxa = f'''
ObjC.import("AppKit");
const pb = $.NSPasteboard.generalPasteboard;
const expectedHtml = {json.dumps(html_table, ensure_ascii=False)};
const expectedText = {json.dumps(plain_text, ensure_ascii=False)};
pb.clearContents;
const htmlSet = pb.setStringForType($(expectedHtml), $.NSPasteboardTypeHTML);
const textSet = pb.setStringForType($(expectedText), $.NSPasteboardTypeString);
const types = pb.types.js.map(item => ObjC.unwrap(item));
const storedHtml = ObjC.unwrap(pb.stringForType($.NSPasteboardTypeHTML));
const storedText = ObjC.unwrap(pb.stringForType($.NSPasteboardTypeString));
JSON.stringify({{
  htmlSet,
  textSet,
  hasHtml: types.includes("public.html"),
  hasText: types.includes("public.utf8-plain-text"),
  htmlMatches: storedHtml === expectedHtml,
  textMatches: storedText === expectedText
}});
'''
    result = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", jxa],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to access macOS clipboard: {result.stderr.strip()}")
    try:
        verification = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("macOS clipboard verification returned invalid output") from error
    if not all(verification.values()):
        failed = ", ".join(key for key, passed in verification.items() if not passed)
        raise RuntimeError(f"macOS clipboard verification failed: {failed}")


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Copy TSV from stdin as an HTML table that Microsoft Teams can paste."
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Render every row as a body row instead of using the first row as headers.",
    )
    return parser


def main() -> int:
    args = argument_parser().parse_args()
    try:
        rows = parse_tsv(sys.stdin.read())
        html_table = render_html(rows, has_header=not args.no_header)
        plain_text = render_plain(rows)
        copy_to_macos_clipboard(html_table, plain_text)
    except (TableInputError, RuntimeError) as error:
        print(f"copy-teams-table: {error}", file=sys.stderr)
        return 1

    print(
        "Copied Teams table to clipboard "
        f"({len(rows)} rows x {len(rows[0])} columns; HTML verified)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
