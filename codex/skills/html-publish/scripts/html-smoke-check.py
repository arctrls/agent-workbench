#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


class SmokeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: set[str] = set()
        self.lang = False
        self.charset = False
        self.viewport = False
        self.title_text = ""
        self.in_title = False
        self.asset_refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.add(tag)
        attr = {name.lower(): value or "" for name, value in attrs}
        if tag == "html" and attr.get("lang", "").strip():
            self.lang = True
        if tag == "meta" and attr.get("charset", "").lower() == "utf-8":
            self.charset = True
        if tag == "meta" and attr.get("name", "").lower() == "viewport":
            self.viewport = bool(attr.get("content", "").strip())
        if tag == "title":
            self.in_title = True
        if tag == "link" and attr.get("href"):
            self.asset_refs.append(("link", attr["href"]))
        if tag == "script" and attr.get("src"):
            self.asset_refs.append(("script", attr["src"]))
        if tag == "img" and attr.get("src"):
            self.asset_refs.append(("img", attr["src"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text += data


def is_remote_or_special(ref: str) -> bool:
    parsed = urlparse(ref)
    return bool(parsed.scheme or parsed.netloc or ref.startswith("#") or ref.startswith("data:"))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: html-smoke-check.py <html-file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]).expanduser()
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    html = path.read_text(encoding="utf-8")
    parser = SmokeParser()
    parser.feed(html)

    errors: list[str] = []
    warnings: list[str] = []

    if not re.search(r"<!doctype\s+html\s*>", html, re.IGNORECASE):
        errors.append("missing <!doctype html>")
    for tag in ("html", "head", "body"):
        if tag not in parser.tags:
            errors.append(f"missing <{tag}>")
    if not parser.lang:
        warnings.append("missing non-empty html lang attribute")
    if not parser.charset:
        warnings.append("missing <meta charset=\"UTF-8\">")
    if not parser.viewport:
        warnings.append("missing viewport meta tag")
    if not parser.title_text.strip():
        warnings.append("missing non-empty <title>")
    if re.search(r"\b(TODO|FIXME)\b", html):
        warnings.append("contains TODO/FIXME marker")

    for tag, ref in parser.asset_refs:
        if is_remote_or_special(ref) or ref.startswith("/"):
            continue
        asset_path = (path.parent / ref.split("?", 1)[0].split("#", 1)[0]).resolve()
        if not asset_path.exists():
            errors.append(f"missing local asset referenced by <{tag}>: {ref}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
