---
name: java-code-style-review
description: Use when reviewing Java code style, Java naming and idioms, fluent accessors, final parameters or locals, DTO/class shape, logging consistency, stream/collection style, or a Java-only style self-review without implementation.
---

# Java Code Style Review

## Overview

Review Java source against the repository's Java code style rules only. Treat the canonical `java-code-style.md` reference as the source of truth and keep findings actionable, scoped, and tied to changed code.

## Workflow

1. Confirm the request is a Java style review or Java self-review task.
2. Identify the Java files under review from the user's scope or `git diff`.
3. Read the canonical rule reference before reviewing:
   - Installed skill path: `../java-spring-workflow/references/java-code-style.md`
   - Repository source path: `codex/skills/java-spring-workflow/references/java-code-style.md`
4. Inspect the target Java files and any nearby project conventions needed to interpret the rules.
5. Report only clear rule violations or intentional exceptions. Do not rewrite code unless the user explicitly asks for fixes.

If the canonical reference is missing, say which path was unavailable and stop instead of inventing replacement rules.

## Review Focus

Use the priority order from `java-code-style.md`. In particular, check:

- fluent record-style accessors instead of getter-style accessors
- `final` on parameters and local variables where surrounding code follows that rule
- unnecessary `@Builder` on simple immutable DTOs
- feature-local logging prefix consistency
- stream and immutable collection usage where it is clearer than manual loops and mutable collectors

Also check the other naming, parameter formatting, exception/logging, conditional/null handling, collections, and class/DTO design rules from the reference when they apply to touched code.

## Boundaries

- Stay in style-review scope. Do not report logic correctness, security, performance, API compatibility, or architecture issues unless the user asks for a broader review.
- Prefer changed or requested Java files over untouched legacy code.
- Cite project rules and nearby conventions, not personal preference.
- Distinguish auto-fixable formatting from manual style changes.
- Avoid trivial bikeshedding when the code is consistent with the project.

## Output Format

Use this structure:

```markdown
## Java Code Style Review

**Overall:** PASS | MINOR ISSUES | MAJOR ISSUES
**Scope:** [files reviewed]
**Rules:** [path to java-code-style.md used]

### Findings
- `path/File.java:42` - [MAJOR] Getter-style accessor `getStatus()` conflicts with the Java code style rule preferring `status()`.

### Auto-Fixable
- [formatter or lint command, if applicable]

### Notes
- [intentional exceptions or missing context]
```
