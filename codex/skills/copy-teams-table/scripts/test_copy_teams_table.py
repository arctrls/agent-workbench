from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("copy_teams_table.py")


class CopyTeamsTableTest(unittest.TestCase):
    def run_script(self, table: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=table,
            capture_output=True,
            check=False,
            text=True,
        )

    def read_clipboard(self) -> dict[str, object]:
        script = r'''
ObjC.import("AppKit");
const pb = $.NSPasteboard.generalPasteboard;
const types = pb.types.js.map(item => ObjC.unwrap(item));
const htmlValue = pb.stringForType($.NSPasteboardTypeHTML);
const textValue = pb.stringForType($.NSPasteboardTypeString);
JSON.stringify({
  types,
  html: htmlValue.isNil() ? null : ObjC.unwrap(htmlValue),
  text: textValue.isNil() ? null : ObjC.unwrap(textValue)
});
'''
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            check=True,
            text=True,
        )
        return json.loads(result.stdout)

    @unittest.skipUnless(sys.platform == "darwin", "macOS pasteboard test")
    def test_copies_html_table_and_plain_text_fallback(self) -> None:
        table = "상점\t미결제 주문 유지기간\nCN\t1시간\nA&B\t<VIP>\n"

        result = self.run_script(table)

        self.assertEqual(0, result.returncode, result.stderr)
        clipboard = self.read_clipboard()
        self.assertIn("public.html", clipboard["types"])
        self.assertIn("public.utf8-plain-text", clipboard["types"])
        self.assertEqual(table.rstrip("\n"), clipboard["text"])
        self.assertIn("<table", clipboard["html"])
        self.assertIn("<th", clipboard["html"])
        self.assertIn("A&amp;B", clipboard["html"])
        self.assertIn("&lt;VIP&gt;", clipboard["html"])
        self.assertNotIn("A&B</td>", clipboard["html"])

    def test_rejects_rows_with_different_column_counts(self) -> None:
        result = self.run_script("A\tB\nonly-one-column\n")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("column", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
