---
description: Convert Markdown to PDF using pandoc and WeasyPrint
argument-hint: <markdown_file_path>
---

# Markdown to PDF Converter

Convert a Markdown file to PDF using pandoc (for HTML conversion) and WeasyPrint (for PDF generation). Output is saved to ~/Downloads.

## Prerequisites

- **pandoc**: `brew install pandoc`
- **weasyprint**: `pipx install weasyprint`

## Task

Convert the specified Markdown file ($ARGUMENTS) to PDF.

## Execution

```bash
#!/bin/bash
set -e

INPUT_FILE="$ARGUMENTS"

# Validate input
if [[ -z "$INPUT_FILE" ]]; then
    echo "Error: No input file specified"
    echo "Usage: /md-to-pdf <markdown_file_path>"
    exit 1
fi

# Expand ~ and resolve path
INPUT_FILE="${INPUT_FILE/#\~/$HOME}"

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: File not found: $INPUT_FILE"
    exit 1
fi

# Check prerequisites
if ! command -v weasyprint &> /dev/null; then
    echo "Error: weasyprint not found. Install with: pipx install weasyprint"
    exit 1
fi

if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc not found. Install with: brew install pandoc"
    exit 1
fi

# Setup paths
FILENAME=$(basename "$INPUT_FILE" .md)
OUTPUT_DIR="$HOME/Downloads"
TEMP_HTML=$(mktemp /tmp/md-to-pdf.XXXXXX.html)
OUTPUT_PDF="$OUTPUT_DIR/${FILENAME}.pdf"

# Handle duplicate files
if [[ -f "$OUTPUT_PDF" ]]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT_PDF="$OUTPUT_DIR/${FILENAME}_${TIMESTAMP}.pdf"
fi

echo "Converting: $INPUT_FILE"

# Create HTML with embedded CSS
cat > "$TEMP_HTML" << 'HTMLHEAD'
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@page { size: A4; margin: 20mm 15mm; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    color: #1a1a1a;
}
h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h3 { font-size: 1.25em; }
p { margin-top: 0; margin-bottom: 16px; }
a { color: #0366d6; text-decoration: none; }
code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 85%;
    background-color: rgba(27,31,35,0.05);
    padding: 0.2em 0.4em;
    border-radius: 3px;
}
pre {
    background-color: #f6f8fa;
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    border-radius: 6px;
}
pre code { background-color: transparent; padding: 0; }
blockquote { margin: 16px 0; padding: 12px 16px; background-color: #f8f9fa; border-left: 4px solid #4a90d9; color: #333; }
blockquote p { margin: 0; }
table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
table th, table td { padding: 10px 13px; border: 1px solid #d0d7de; }
table th { background-color: #f6f8fa; font-weight: 600; }
table tr:nth-child(even) { background-color: #f6f8fa; }
ul, ol { padding-left: 2em; margin-top: 0; margin-bottom: 16px; }
li + li { margin-top: 0.25em; }
hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #d0d7de; border: 0; }
</style>
</head>
<body>
HTMLHEAD

# Convert markdown to HTML body and append
pandoc "$INPUT_FILE" -f markdown -t html >> "$TEMP_HTML"

# Close HTML
echo "</body></html>" >> "$TEMP_HTML"

# Convert to PDF using WeasyPrint
weasyprint "$TEMP_HTML" "$OUTPUT_PDF"

# Cleanup
rm -f "$TEMP_HTML"

echo "Done: $OUTPUT_PDF"
```

Run the above bash script with the provided file path.
