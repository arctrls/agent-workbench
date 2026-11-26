---
name: finder-reveal
description: Reveal a local file or open a folder in macOS Finder. Use for requests such as "Finder로 열어", "파인더에서 보여줘", "파일 위치 열어", "저장된 폴더 열어", or "$finder-reveal" when the user wants to locate an artifact rather than open its contents in an editor or viewer.
---

# Finder Reveal

Show the requested local artifact in Finder using macOS `/usr/bin/open`.

## Workflow

1. Resolve the target from the explicit path or the current conversation's artifact. When the user says "Finder로 열어" after a file was created, use that file. Ask only when multiple targets remain equally plausible.
2. Expand `~`, resolve relative paths against the relevant workspace, and confirm the target exists. Do not create a missing target.
3. Choose the action:
   - **File or a request to show an item's location:** reveal and select the item in its parent folder with `/usr/bin/open -R`.
   - **Folder whose contents the user wants to see:** open it with `/usr/bin/open -a Finder`.
4. Pass the absolute path as one safely quoted argument. Preserve spaces and Korean characters; avoid evaluating path text as shell code.
5. Check the command's exit status and briefly report the result. Report a missing path, unsupported OS, or command failure directly.

```bash
# Select a file in its containing folder.
/usr/bin/open -R '/absolute/path/검증 보고서.pdf'

# Open a folder's contents in Finder.
/usr/bin/open -a Finder '/absolute/path/결과 파일'
```

Use the native command directly; browser or GUI automation is unnecessary. This skill locates files without editing them or launching their default viewer. A request to read a PDF or edit a file belongs to that application's workflow.
