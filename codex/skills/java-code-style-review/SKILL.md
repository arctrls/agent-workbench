---
name: java-code-style-review
description: Review Java naming, readability, method composition, and DTO shape using project rules and existing static-check evidence. Use for Java style reviews or style self-reviews without implementation.
---

# Java Code Style Review

## Overview

Review Java source against the repository's Java code style rules only. Treat the canonical `java-code-style.md` reference as the source of truth and keep findings actionable, scoped, and tied to changed code.

## Workflow

1. Confirm the request is a Java style review or Java self-review task.
2. Identify the Java files under review from the user's scope or `git diff`.
3. Read the shared [static-check and review boundary](../java-spring-workflow/references/jvm-review-checks.md), then the canonical Java rule reference:
   - Installed skill path: `../java-spring-workflow/references/java-code-style.md`
   - Repository source path: `codex/skills/java-spring-workflow/references/java-code-style.md`
4. Discover and run the project's configured checks. Record their scope, exclusions, and results; do not install tools or auto-fix during a read-only review.
5. Inspect the target Java files and nearby conventions for context-dependent readability issues. Report only clear violations or intentional exceptions, without duplicating tool diagnostics. Do not rewrite code unless fixes are requested.

If the canonical reference is missing, say which path was unavailable and stop instead of inventing replacement rules.

## Review Focus

Use the priority order from `java-code-style.md`. In particular, check:

- fluent record-style accessors instead of getter-style accessors
- composed methods at a single abstraction level, without unnecessary forwarding helpers
- business-intent names at use-case level and SQL-oriented names only where persistence details belong
- processing steps and guard clauses whose presentation obscures intent; configured spacing, imports, and `final` checks belong in tool results
- unnecessary `@Builder` on simple immutable DTOs
- feature-local logging conventions when not already covered by configured checks
- stream and immutable collection usage where it is clearer than manual loops and mutable collectors

Also check the other naming, parameter formatting, exception/logging, conditional/null handling, collections, and class/DTO design rules from the reference when they apply to touched code.

## Boundaries

- Stay in style-review scope. Do not report logic correctness, security, performance, API compatibility, or architecture issues unless the user asks for a broader review.
- Prefer changed or requested Java files over untouched legacy code.
- Cite project rules and nearby conventions, not personal preference.
- Distinguish auto-fixable formatting from manual style changes.
- Treat getter-style accessors and `@Builder` as candidates until framework contracts and project exceptions are checked. Method length or complexity alone does not justify extraction.
- Avoid trivial bikeshedding when the code is consistent with the project.

## Output Format

Use this structure:

```markdown
## Java Code Style Review

**Overall:** PASS | MINOR ISSUES | MAJOR ISSUES
**Scope:** [files reviewed]
**Rules:** [path to java-code-style.md used]

### Tool Results
- [command, checked scope, outcome; missing or excluded checks]

### Contextual Findings
- `path/File.java:42` - [severity, applicable rule, concrete readability problem, and smallest correction]

### Notes
- [intentional exceptions or missing context]
```
