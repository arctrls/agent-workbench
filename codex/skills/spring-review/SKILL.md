---
name: spring-review
description: Review existing Java or Kotlin Spring code through one entry point that combines configured checks, design and behavior review, and language-specific style review into one report. Use for a package, API feature, diff, commit range, or implementation handoff.
---

# Spring Review

Use this as the single entry point for a complete Spring review. Code need not have been developed with `spring-workflow`. A review-only request does not authorize source edits, auto-formatting, new tests, baseline changes, commits, or pushes. Existing implementation or fix authorization still applies, but keep review findings distinct from subsequent fixes.

## Establish scope and criteria

- Accept a package, API feature, diff, commit range, or handoff from [spring-workflow](../spring-workflow/SKILL.md). For a handoff, reuse the implementation's change contract, diff, applicable rule sources, and check results for the reviewed code state.
- If the user identifies work by time or feature rather than a path, inspect Git history and the working tree to identify candidate packages. State the selected scope and comparison base. Do not assume all commits from that period belong to the requested feature; ask only when material ambiguity remains.
- For a package review, inspect the whole requested package and relevant callers, persistence code, and tests. For a diff review, prioritize new or worsened problems and existing defects that affect the change. Distinguish pre-existing findings from introduced regressions; if history is unavailable, do not guess their origin.
- Read project instructions and design decisions, then the shared [checks and review evidence](../spring-workflow/references/jvm-review-checks.md). Project choices take precedence over reference defaults. Do not apply another repository's architecture automatically.

## Coordinate the review

1. **Check once.** Inspect build/test configuration and existing evidence. Run relevant configured checks that are missing or stale, within the authorized environment; do not run live operational probes as ordinary tests. Record commands, scope, exclusions, and results. Keep this evidence available to all review passes rather than rerunning the same checks.
2. **Review design and behavior.** Follow [spring-design-review](../spring-design-review/SKILL.md), including its canonical Spring rules, to assess responsibilities, boundaries, dependencies, and runtime contracts. Rule compliance alone does not prove behavior correct.
3. **Review the relevant languages.** Follow [Java style review](../java-code-style-review/SKILL.md) for Java and [Kotlin style review](../kotlin-code-style-review/SKILL.md) for Kotlin. Include both for mixed boundaries. Reuse their canonical references and the check evidence; do not create separate copies of their criteria.
4. **Review extended workflows when needed.** Apply [legacy feature extension review](../legacy-feature-extension-review/SKILL.md) when an existing operational flow gains a new path or state. Do not run every specialized review regardless of relevance.
5. **Consolidate.** Return one report instead of separate skill reports. Deduplicate findings about the same cause and do not repeat formatter diagnostics as manual findings. Review passes do not require separate agents or additional user invocations.

## Unified result and handoff

Lead with material findings, ordered by impact. Include:

- The reviewed scope, code state/comparison base, and criteria used.
- For each finding: `file:line`, applicable rule or behavior contract, concrete trigger, impact, and smallest useful correction. Use the shared categories: rule violation, behavior defect, or improvement proposal. Identify pre-existing issues when established.
- One summary of automated evidence, justified exceptions, unresolved questions, and unverified scope. State when no material findings were found without implying unverified behavior passed.

For review-only work, stop after reporting. For an implementation handoff, return findings to `spring-workflow` for authorized fixes and affected checks; review the resulting changes again as needed. Implementation being finished starts review, while task completion follows resolution of material findings and disclosure of verification limits. Optional improvement proposals do not automatically block completion.
