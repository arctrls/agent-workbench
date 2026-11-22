# Static Checks and JVM Review

Use this boundary for Java, Kotlin, and Spring reviews and implementation self-reviews. Project configuration and explicit user decisions take precedence over suggested tools.

## Establish what the tools actually checked

- Inspect the build, formatter/linter configuration, test engine, CI tasks, and exclusions before reviewing. Run the existing check commands within the authorized scope. A missing, skipped, or failed-to-start check is unverified, not a pass.
- Keep configuration at project level, sharing it across modules where appropriate. Package-specific architecture constraints belong in rules, not a separate tool installation per package.
- For mixed Java/Kotlin projects, Spotless can coordinate a Java formatter and ktlint. Calling `ktlint()` in Spotless selects the engine; do not add a separate ktlint plugin/task for the same checks. Pin formatter versions when configuring reproducible checks.
- Do not require a fixed tool stack in every repository. Checkstyle, detekt, SpotBugs, and Error Prone are optional according to the project's language, compatibility, and remaining coverage. Avoid overlapping formatting and lint rules.
- Spring Modulith verifies the agreed module arrangement; use ArchUnit for additional project rules instead of repeating Modulith's cycle and internal-access checks. Use the project's actual test engine; JUnit annotations alone do not run under a Kotest-only configuration.
- Installing tools, changing rules, regenerating baselines, or auto-formatting is implementation work. A review request alone does not authorize it.

## Classify evidence

| Evidence | Review responsibility |
| --- | --- |
| Deterministic configured rule: formatting, imports, name casing, types | Summarize the command, scope, and result once. Do not repeat every diagnostic as a manual finding. |
| Candidate: long method, complexity, `@Builder`, `now()`, broad catch, concrete dependency | Inspect applicability and exceptions. Presence or a threshold alone does not establish a defect. |
| Context: business-intent naming, abstraction level, ownership, necessary layers | Explain the concrete reading or maintenance problem and the smallest useful correction. |
| Runtime contract: transaction participation, rollback, retry, serialization, external side effects | Trace the code and use relevant integration evidence. Static checks cannot prove runtime behavior. |

Passing architecture rules proves compliance with those rules, not that the selected architecture is appropriate. Do not recommend abstractions or method extraction solely to satisfy a metric or a named design principle.

## Existing codebases

- Prioritize new or worsened violations. Report pre-existing defects when they affect the requested change; do not turn a local change into a repository-wide cleanup.
- Introduce new checks in report mode or a narrow scope first, review false positives, then enforce agreed rules. Keep serious correctness/security defects visible even when they predate adoption.
- Where supported, record existing violations in a versioned baseline and fail on new identities, not only a total-count increase. Do not automatically regenerate or enlarge the baseline to make a check pass. Remove resolved entries through review.
- Spotless ratcheting selects changed **files**, not changed lines. Separate large formatting changes from behavioral changes. Use a deliberate baseline ref; ensure CI has that ref and does not compare a commit to itself.
- An exclusion is an unverified scope. Document the reason and keep it narrow; do not exclude whole business modules merely to obtain a passing result.

## Report

Separate tool results, contextual findings, and verification limits. For a manual finding give `file:line`, the applicable rule or contract, the trigger or reading problem, and its impact. Do not duplicate tool findings or claim an unexecuted check passed.
