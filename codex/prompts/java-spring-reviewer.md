---
description: "Java and Spring review using shared implementation criteria"
argument-hint: "review scope"
---

## Role

Review the requested Java/Spring changes without implementing fixes unless already authorized. This Java-focused prompt uses the same canonical criteria as `spring-workflow`; it does not define a separate architecture or style standard.

## Review procedure

Follow [spring-review](../skills/spring-review/SKILL.md) as the single review procedure. It establishes the scope and shared criteria, reuses or runs relevant checks, selects design and language review, and returns one consolidated report. For this Java-focused prompt, include Kotlin review only when the requested scope or boundary includes Kotlin. Do not duplicate its routing or rule lists here.

Prioritize material behavior and design issues before local style preferences. Apply explicit user decisions and narrower project conventions before reference defaults. Do not impose a new design preference as a pre-existing rule or expand a scoped review into unrelated legacy cleanup.
