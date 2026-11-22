---
name: kotlin-code-style-review
description: Review Kotlin naming, readability, method composition, data types, and Java interoperability using project conventions and static-check evidence. Use for Kotlin style reviews or self-reviews without implementation.
---

# Kotlin Code Style Review

Review changed or requested Kotlin code for meaning and readability. Stay read-only unless fixes are requested; do not expand a style review into an architecture or correctness audit.

## Workflow

1. Read the project instructions, the diff, nearby Kotlin conventions, and the shared [static-check and review boundary](../java-spring-workflow/references/jvm-review-checks.md).
2. Inspect Gradle/Maven, `.editorconfig`, Spotless/ktlint, detekt, and existing test configuration. Run the configured checks and record their actual coverage. Do not require tools absent from the project.
3. Review context-dependent naming and readability. In mixed code, inspect Java callers and framework constraints before suggesting a language-specific rewrite.
4. Report tool results once, then manual findings with `file:line`, the applicable convention, the concrete reading problem, and a minimal correction. State missing checks and intentional exceptions separately.

## Contextual Review

- Keep orchestration at one abstraction level. Extract a method when its name explains a meaningful operation; do not create forwarding helpers solely to shorten code.
- Use names that expose business intent, state changes, and units. Do not substitute a casing violation already reported by a linter for semantic naming review.
- Check whether nested scope functions, chained nullable operations, implicit `it` receivers, or expression bodies obscure control flow. Do not ban these constructs or replace clear loops with pipelines mechanically.
- Prefer `val` where appropriate, but distinguish an immutable reference from an immutable object or collection. A read-only Kotlin collection type alone does not prove immutable contents.
- Choose properties, constructors, and `data class` shapes for the actual contract. Do not port Java `final`, record-accessor, Stream, Yoda-comparison, or builder rules mechanically into Kotlin.
- Consider Java callers, generated accessors, nullability annotations, and framework requirements before changing a boundary type's shape. If API correctness is in question, flag the need for broader review rather than claiming style checks prove compatibility.
- Kotlin `internal` is scoped to the compilation module, not the package or a Spring Modulith module. Do not report it as proof of feature encapsulation; architecture checks need explicit package/API rules.

## Existing Code

Focus on new or worsened issues and existing problems that affect the requested change. Preserve the project's chosen style, avoid repository-wide cleanup, and treat complexity metrics as inspection signals rather than automatic refactoring requirements.
