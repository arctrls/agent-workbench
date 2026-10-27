---
name: markdown-preview
description: Open a local Markdown file as a styled HTML preview in the browser, including tables, code blocks, and Mermaid diagrams. Use for $markdown-preview, Markdown 미리보기, or requests to preview a document just created. Produces a static snapshot rather than a live editor or PDF.
license: Apache-2.0
---

# Markdown Preview

Preview a Markdown file using the bundled rp1-derived HTML templates.

## Workflow

1. Resolve the file explicitly named by the user. If no path is given, use the
   user-facing Markdown document most recently created or discussed in this
   conversation, excluding this skill's setup files unless explicitly requested.
   Ask only if the target is still ambiguous.
2. Resolve this skill directory from the loaded `SKILL.md` path. Run the bundled
   script from the user's workspace so relative input paths keep their meaning:

   ```bash
   python3 /absolute/path/to/markdown-preview/scripts/preview.py "/path/to/document.md"
   ```

3. Read the JSON result and report the source file and whether the browser was
   opened. A successful launcher does not prove that browser rendering completed;
   inspect the page if the user reports an issue or visual verification is required.
4. To refresh after edits, rerun the command. This is a static HTML snapshot,
   not a live-reloading server or the Neovim `:MarkdownPreview` command.

## Options

- `--theme github` (default), `--theme dark`, or `--theme minimal`.
- `--title "Document title"` sets the browser tab title.
- `--no-open` creates the preview without launching the browser, for validation
  or when the user only requests the HTML artifact.

For pasted Markdown, write it to a temporary `.md` file and preview that file.
Wrap standalone Mermaid source in a `mermaid` code fence before previewing it.

## Behavior

- Requires Python 3; no Python packages or rp1 CLI installation are needed.
- Reuse `scripts/preview.py` and [TEMPLATES.md](TEMPLATES.md), rather than building
  a new renderer for each invocation.
- Source files are read without editing or saving an open editor buffer. Output
  is a uniquely named HTML file in the system temporary directory, with mode 0600.
- HTML rendering uses version-pinned marked.js, DOMPurify, Mermaid, and, for
  GitHub/dark themes, Prism from jsDelivr. Network access is needed to load them;
  do not describe the preview as fully offline or as containing embedded libraries.
- Mermaid validation happens during browser rendering. Do not claim a separate
  CLI validation happened, or rewrite the user's diagrams merely to preview them.
- Relative links and images resolve from the source document's directory.
- If generation fails, report the actual error. If the browser cannot be opened,
  provide the generated HTML path instead of claiming it was shown.

## Provenance

Adapted from [rp1-run/rp1 markdown-preview](https://github.com/rp1-run/rp1/tree/main/plugins/base/skills/markdown-preview).
See [NOTICE](NOTICE) for the source revision and changes, and [LICENSE](LICENSE)
for the upstream Apache-2.0 license.
