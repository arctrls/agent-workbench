---
name: gradle-integration-test
description: Use for Gradle projects that have an integrationTest task. This skill runs only integrationTest, keeps ApprovalTests quiet with approvaltests.quiet=true, narrows runs with --tests when useful, and summarizes failures from Gradle/JUnit output and generated reports.
---

# Gradle Integration Test

Use this skill when working in a Gradle project and the user wants to run or
analyze the `integrationTest` task.

## Scope

- Focus only on `integrationTest`.
- Do not run `test`, `check`, or other custom test tasks unless the user
  explicitly asks for them.
- Use focused `--tests` filters when a class or method is known.

## Commands

Run from the Gradle project root.

Default full integration test run:

```bash
./gradlew integrationTest -Dapprovaltests.quiet=true
```

Focused class run:

```bash
./gradlew integrationTest --tests 'com.ktown4u.example.SomeIntegrationTest' -Dapprovaltests.quiet=true
```

Focused method run:

```bash
./gradlew integrationTest --tests 'com.ktown4u.example.SomeIntegrationTest.some_test_method' -Dapprovaltests.quiet=true
```

## ApprovalTests

Always pass `-Dapprovaltests.quiet=true` when running `integrationTest`.
This keeps ApprovalTests from launching an interactive diff reporter in
projects that wire the `approvaltests.quiet` system property into their test
runtime.

When an approval test fails:

- Do not approve or overwrite snapshots unless the user explicitly asks.
- Inspect the `.received.*` and `.approved.*` files referenced by the failure.
- Explain whether the diff looks like an intentional behavior change,
  nondeterministic output, fixture drift, or a regression.
- Mention exact received/approved file paths in the final summary.

## Result Analysis

After each run:

- Report the command that was run.
- State pass/fail status and the failing test class/method names.
- Use Gradle output first, then inspect
  `build/test-results/integrationTest/TEST-*.xml` or
  `build/reports/tests/integrationTest/` when the console output is truncated.
- Summarize the first actionable failure cause before secondary noise.
- If the run could not start because of environment setup, dependency auth, or
  database/service availability, say that clearly and include the blocking
  error.
