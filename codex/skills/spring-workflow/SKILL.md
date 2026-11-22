---
name: spring-workflow
description: Implement Java or Kotlin Spring changes against shared design and language rules, then check, review, fix, and verify the result. Use for a concrete implementation request or an agreed plan.
---

# Spring Workflow

Coordinate implementation and review for Java, Kotlin, or mixed Spring projects. Start from the user's concrete request; a separate approved plan is not required when the request already establishes the behavior and scope. For open design questions, establish the relevant decisions before dependent implementation. A review-only request starts directly at [spring-review](../spring-review/SKILL.md) without an implementation phase.

The normal sequence is **implementation and relevant checks → `spring-review` → resolve findings → task completion**. Finishing implementation triggers review; it is not yet the completion report.

See the Korean [implementation and review overview](references/workflow-overview.md) for the full flow and responsibility map.

## Shared criteria

Before implementation, read the project instructions and relevant design decisions, then:

- [Spring design rules](references/spring-framework-rules.md) for structure, interfaces, time, transactions, and dependency direction.
- [Java style](references/java-code-style.md) for changed Java source.
- [Kotlin style](references/kotlin-code-style.md) for changed Kotlin source. In mixed boundaries inspect both callers and implementations.
- [Checks and review evidence](references/jvm-review-checks.md) for the project's actual automated coverage and the remaining review work.

These references are shared with reviewers; do not maintain a second rule list in this workflow. Explicit user decisions and narrower project rules precede reference defaults. A project's choice such as combined controller/use-case classes or `conversation.spi` is not a universal Spring requirement.

## Implementation and review loop

1. **Establish the change contract.** Identify the intended behavior, owning module/use case, relevant rules and their sources, behavior to preserve, and the checks that can establish completion. Reuse the existing plan or issue. For a small change, a brief statement is enough; do not generate a mandatory plan artifact.
2. **Check the existing implementation and coverage.** Inspect comparable use cases and boundary callers. Protect missing business or regression coverage before changing behavior, following the project's fail-first requirements. Preserve transactions, authorization, serialization, deduplication, external-call order, and cleanup where they apply.
3. **Implement within that contract.** Apply structural rules while choosing the interface and package, not only during cleanup. Keep the diff scoped; do not add forwarding layers, speculative abstractions, or unrelated legacy cleanup.
4. **Run configured checks.** Use the project's formatter, compiler, architecture checks, and behavior tests as appropriate. Record commands, checked scope, exclusions, and results. Do not install a prescribed tool stack or expand baselines merely to get a pass.
5. **Hand the implemented change to [spring-review](../spring-review/SKILL.md).** Provide the change contract, reviewed diff/code state, applicable rule sources, and check evidence. It coordinates design, behavior, and relevant language review and returns one consolidated report. Do not ask the user to invoke each review separately or rerun unchanged checks merely because a different review pass is starting.
6. **Resolve findings.** Within an implementation request, fix clear defects and applicable rule violations, then rerun affected checks and return the changed scope to `spring-review` as needed. If a finding changes the agreed design, resolve that decision before dependent work. Record justified exceptions; keep optional improvements separate. Unchanged passing checks need not be repeated.
7. **Report completion evidence.** State what changed, the applicable criteria and any exceptions, tool/test results, unresolved findings, and verification limits. Commit, push, publish, or deploy only within the user's authorized scope.

## Review outcomes

Use the shared [finding categories](references/jvm-review-checks.md#finding-categories) in self-review and standalone review. A rule violation needs an applicable source; a behavior defect needs a concrete failure path; a new design preference is an improvement proposal. Passing rules does not by itself establish correct behavior or a suitable design.
