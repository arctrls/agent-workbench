# Kotlin Code Style

Use the same reference for Kotlin implementation and style review. Explicit user decisions, project rules, framework requirements, and existing caller contracts precede these defaults. Use configured diagnostics for formatting; these criteria require context.

## Meaning and method composition

- Keep orchestration at one abstraction level. Extract a method when its name explains a meaningful operation; do not create forwarding helpers solely to shorten code.
- Use names that expose business intent, state changes, and units. A casing violation already reported by a linter is not a semantic naming finding.
- Check whether nested scope functions, chained nullable operations, implicit `it` receivers, or expression bodies obscure control flow. Do not ban these constructs or replace clear loops with pipelines mechanically.

## Data and interoperability

- Prefer `val` where appropriate, but distinguish an immutable reference from an immutable object or collection. A read-only Kotlin collection type alone does not prove immutable contents.
- Choose properties, constructors, and `data class` shapes for the actual contract. Do not port Java `final`, record-accessor, Stream, Yoda-comparison, or builder rules mechanically into Kotlin.
- Consider Java callers, generated accessors, nullability annotations, and framework requirements before changing a boundary type's shape. Style checks do not establish API compatibility; correctness questions require broader review and relevant tests.
- Kotlin `internal` is scoped to the compilation module, not the package or a Spring Modulith module. Feature encapsulation requires the project's explicit package/API rules and architecture checks.

## Existing code

Focus on new or worsened issues and existing problems that affect the requested change. Preserve the project's chosen style, avoid repository-wide cleanup, and treat complexity metrics as inspection signals rather than automatic refactoring requirements.
