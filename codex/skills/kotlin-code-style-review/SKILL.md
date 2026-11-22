---
name: kotlin-code-style-review
description: Review Kotlin naming, readability, method composition, data types, and Java interoperability using project conventions and static-check evidence. Use for Kotlin style reviews or self-reviews without implementation.
---

# Kotlin Code Style Review

Review changed or requested Kotlin code for meaning and readability. Stay read-only unless fixes are requested; do not expand a style review into an architecture or correctness audit.

## Workflow

1. Read the project instructions, the diff, nearby Kotlin conventions, and the shared [static-check and review boundary](../spring-workflow/references/jvm-review-checks.md).
2. Inspect Gradle/Maven, `.editorconfig`, Spotless/ktlint, detekt, and existing test configuration. Run the configured checks and record their actual coverage. Do not require tools absent from the project.
3. Review context-dependent naming and readability. In mixed code, inspect Java callers and framework constraints before suggesting a language-specific rewrite.
4. Report tool results once, then manual findings with `file:line`, the applicable convention, the concrete reading problem, and a minimal correction. State missing checks and intentional exceptions separately.

## Canonical criteria

Read the shared [Kotlin style reference](../spring-workflow/references/kotlin-code-style.md) before judging the code. Implementation through `spring-workflow` uses this same reference. Apply project conventions and boundary contracts before reference defaults; do not maintain a separate style rule list here.

Use the shared [finding categories](../spring-workflow/references/jvm-review-checks.md#finding-categories). A new preference is an improvement proposal, not an existing rule violation. If the canonical reference is unavailable, report the missing path rather than inventing criteria.

## Existing Code

Focus on new or worsened issues and existing problems that affect the requested change. Preserve the project's chosen style, avoid repository-wide cleanup, and treat complexity metrics as inspection signals rather than automatic refactoring requirements.
