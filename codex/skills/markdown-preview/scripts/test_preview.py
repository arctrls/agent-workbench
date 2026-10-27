"""Run with python3 -B -m unittest discover -s scripts -p 'test_preview.py'."""

import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("preview.py")


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="markdown-preview-test-")
        self.addCleanup(self.workspace.cleanup)
        self.source = Path(self.workspace.name) / "한글 문서.md"

    def run_preview(self, text, *args):
        self.source.write_text(text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.source), "--no-open", *args],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        path = Path(response["filePath"])
        self.addCleanup(path.unlink, missing_ok=True)
        self.assertTrue(path.is_file())
        self.assertFalse(response["browserOpened"])
        self.assertEqual(self.source.read_text(encoding="utf-8"), text)
        return path, path.read_text(encoding="utf-8")

    def test_each_theme_preserves_markdown_and_relative_asset_origin(self):
        markdown = "# 한글 제목\n\n| 상품 | 날짜 |\n| --- | --- |\n| 케이스타일 | 숨김 |\n\n![그림](image.png)\n"
        for theme in ("github", "dark", "minimal"):
            with self.subTest(theme=theme):
                path, document = self.run_preview(markdown, "--theme", theme)
                payload = re.search(
                    r'<script type="application/json" id="markdown-source">\s*(.*?)\s*</script>',
                    document, re.DOTALL,
                )
                self.assertIsNotNone(payload)
                data = json.loads(payload.group(1))
                self.assertEqual(data["markdown"], markdown)
                self.assertEqual(data["sourceUrl"], self.source.resolve().as_uri())
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_document_text_cannot_escape_payload_or_replace_template_tokens(self):
        markdown = '</script><script>window.previewInjected=true</script>\n{{TITLE}} {{MARKDOWN_DATA}}'
        _, document = self.run_preview(markdown, "--title", '<img src=x onerror="alert(1)">')
        payload = re.search(
            r'<script type="application/json" id="markdown-source">\s*(.*?)\s*</script>',
            document, re.DOTALL,
        )
        self.assertIsNotNone(payload)
        self.assertEqual(json.loads(payload.group(1))["markdown"], markdown)
        self.assertNotIn('<script>window.previewInjected', document)
        title = re.search(r'<title>(.*?)</title>', document).group(1)
        self.assertNotIn('<img', title)
        self.assertIn('&lt;img', title)

    def test_repeated_preview_creates_distinct_files_and_empty_input_is_valid(self):
        first, _ = self.run_preview("")
        second, _ = self.run_preview("")
        self.assertNotEqual(first, second)

    def test_missing_source_returns_error_without_success_output(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.source), "--no-open"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Preview failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
