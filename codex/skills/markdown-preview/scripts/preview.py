#!/usr/bin/env python3
"""Open a static Markdown preview using the rp1-derived HTML templates."""

import argparse
import html
import json
from pathlib import Path
import re
import sys
import tempfile
import webbrowser


THEMES = ("github", "dark", "minimal")
TEMPLATES = Path(__file__).resolve().parent.parent / "TEMPLATES.md"


def render(source: Path, theme: str, title: str) -> str:
    templates = re.findall(r"```html\n(.*?)\n```", TEMPLATES.read_text(encoding="utf-8"), re.DOTALL)
    if len(templates) != len(THEMES):
        raise ValueError("Expected github, dark, and minimal HTML templates")
    data = json.dumps(
        {"markdown": source.read_text(encoding="utf-8"), "sourceUrl": source.as_uri()},
        ensure_ascii=False,
    ).replace("<", "\\u003c").replace("&", "\\u0026")
    replacements = {"TITLE": html.escape(title), "MARKDOWN_DATA": data}
    return re.sub(
        r"\{\{(TITLE|MARKDOWN_DATA)\}\}",
        lambda match: replacements[match.group(1)],
        templates[THEMES.index(theme)],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Markdown file; relative paths use the current directory")
    parser.add_argument("--theme", choices=THEMES, default="github")
    parser.add_argument("--title", help="Browser tab title; defaults to the source filename")
    parser.add_argument("--no-open", action="store_true", help="Generate HTML without opening a browser")
    args = parser.parse_args()
    try:
        source = args.file.expanduser().resolve(strict=True)
        document = render(source, args.theme, args.title or source.name)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix="markdown-preview-", suffix=".html", delete=False,
        ) as output:
            output.write(document)
            output_path = Path(output.name)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Preview failed: {error}", file=sys.stderr)
        return 1

    opened = False
    if not args.no_open:
        try:
            opened = webbrowser.open(output_path.as_uri(), new=2)
        except (OSError, webbrowser.Error) as error:
            print(f"Browser could not be opened: {error}", file=sys.stderr)
    print(json.dumps({
        "filePath": str(output_path),
        "sourcePath": str(source),
        "theme": args.theme,
        "browserOpened": opened,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
