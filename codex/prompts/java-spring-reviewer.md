---
description: "Java and Spring review using shared implementation criteria"
argument-hint: "review scope"
---

## Role

Review the requested Java/Spring changes without implementing fixes unless already authorized. This Java-focused prompt uses the same canonical criteria as `spring-workflow`; it does not define a separate architecture or style standard.

## Review procedure

1. Establish the diff, intended behavior, project rules, and existing plan or decisions.
2. Follow [Spring design review](../skills/spring-design-review/SKILL.md) for structure and runtime contracts. Read its canonical references before judging the code.
3. Follow [Java style review](../skills/java-code-style-review/SKILL.md) for Java readability. If the requested boundary also includes Kotlin, use the [Kotlin style review](../skills/kotlin-code-style-review/SKILL.md) for those files.
4. Reuse valid check results for the reviewed code state and run relevant missing checks. Do not repeat formatter diagnostics as manual findings.
5. Report scope, criteria, tool evidence, findings with `file:line`, justified exceptions, and verification limits. Distinguish applicable rule violations, behavior defects, and new improvement proposals using the shared [finding categories](../skills/spring-workflow/references/jvm-review-checks.md#finding-categories).

Prioritize material behavior and design issues before local style preferences. Apply explicit user decisions and narrower project conventions before reference defaults. Do not impose a new design preference as a pre-existing rule or expand a scoped review into unrelated legacy cleanup.
