---
name: spring-design-review
description: Review Java or Kotlin Spring changes against the agreed behavior, project architecture, and shared design rules. Use for design review or an implementation self-review covering module boundaries and runtime contracts.
---

# Spring Design Review

Review without editing unless implementation or fixes are already authorized. Do not turn a design review into unrelated style cleanup or a repository-wide audit.

## Criteria and evidence

1. Establish the requested diff and behavior from the user request or existing plan. Read project instructions, applicable design decisions, boundary callers, and the relevant existing behavior.
2. Read the canonical [Spring design rules](../spring-workflow/references/spring-framework-rules.md) and [checks and review evidence](../spring-workflow/references/jvm-review-checks.md). Apply project decisions before reference defaults. Do not invent a second standard for the reviewer.
3. Inspect existing diagnostic and test evidence for the reviewed code state. Run relevant missing checks; do not duplicate unchanged checks or infer success from configuration alone. A failed-to-start or excluded check remains unverified.
4. Compare the implementation with the change contract: use-case responsibility, boundary ownership, module dependencies, time semantics, and transaction/concurrency requirements. Trace authorization, rollback, deduplication, retry, serialization, and external effects where the change can affect them. Architecture checks establish structural compliance, not runtime correctness.
5. For each material finding, give `file:line`, the applicable rule or behavior contract, the concrete trigger or dependency, impact, and the smallest useful correction. Distinguish [rule violations, behavior defects, and improvement proposals](../spring-workflow/references/jvm-review-checks.md#finding-categories). A reasonable exception is not a violation solely because it differs from a reference default.

Report the scope and criteria used, tool evidence, findings, justified exceptions, and verification limits. State when no material findings remain without claiming unverified behavior is proven. Route language-specific readability review to the Java or Kotlin style skill only when included in the requested scope.
