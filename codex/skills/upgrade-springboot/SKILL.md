---
name: upgrade-springboot
description: Plan and execute Spring Boot version upgrades for Gradle or Maven Java/Spring projects. Use when the user asks to upgrade Spring Boot, move to Spring Boot 4 or another target version, update Spring Boot patch/minor versions, handle Spring Boot migration guides, or address related framework changes such as Jackson 3, Spring Framework, Spring Security, Spring Kafka, MyBatis, Flyway, Gradle, Kotlin, or Java compatibility.
---

# Spring Boot Upgrade

Use this skill to upgrade Spring Boot safely, with official documentation checks, dependency compatibility review, staged implementation, and verification evidence.

## Core Rules

- Inspect the repository before choosing an upgrade path.
- Check official Spring documentation before claiming target-version behavior.
- Prefer current-major latest patch/minor before a major upgrade.
- Keep changes staged and reviewable; split PRs when the upgrade crosses major versions or toolchain boundaries.
- Verify after each meaningful stage. Do not claim success from version edits alone.
- Preserve existing behavior unless the user explicitly accepts a breaking change.

## Initial Assessment

Collect the current state from the project root.

For Gradle, inspect:

- `build.gradle.kts` or `build.gradle`
- `settings.gradle.kts` or `settings.gradle`
- `gradle/wrapper/gradle-wrapper.properties`
- `.java-version`, `.jvmrc`, `.sdkmanrc`
- `Dockerfile`, `compose.yml`, `docker-compose.yml`
- `.github/workflows/*.yml` and `.github/workflows/*.yaml`

For Maven, inspect:

- `pom.xml`, parent POMs, and module POMs
- `.mvn/`, Maven wrapper files, and CI workflow Java settings

Report a compact baseline table:

```text
| Component | Current | Source |
| --- | --- | --- |
| Spring Boot | x.y.z | build.gradle.kts |
| Java | x | toolchain / CI / Dockerfile |
| Gradle or Maven | x.y.z | wrapper |
| Kotlin | x.y.z | build script |
| Dependency management | x.y.z | build script |
```

Also identify major Spring-adjacent dependencies:

- Spring Cloud
- Spring Modulith
- Spring Kafka
- Spring Security
- MyBatis Spring Boot Starter
- Flyway
- Hibernate/JPA
- QueryDSL
- springdoc-openapi
- Jackson custom configuration
- test libraries and Spring Boot test slices

## Target Selection

If the user names an exact target version, use it as the target after checking compatibility.

If the user asks for "latest" or does not name a version, verify the latest stable Spring Boot line from official Spring sources before choosing. Do not rely on memory.

For major upgrades, produce the recommended path before editing:

```text
Recommended path:
1. Current Spring Boot line -> latest compatible patch/minor in the same major line
2. Toolchain prerequisites: Java, Gradle or Maven, Kotlin as needed
3. Deprecation cleanup on the current major line
4. Spring Boot major upgrade
5. Breaking-change fixes and warning cleanup
```

Ask before collapsing multiple risky stages into one PR unless the user explicitly requested a single PR or autonomous completion.

## Documentation Checks

Use primary sources for version-specific claims:

- Spring Boot release notes and migration guide for the target version
- Spring Framework release notes when crossing Spring Framework major versions
- Spring Security migration notes when security is present
- Spring Kafka documentation when Kafka listeners or retry topics are present
- Jackson release notes when crossing to Jackson 3
- Dependency compatibility matrices for Spring Cloud, MyBatis, Flyway, Spring Modulith, and springdoc

Summarize only actionable findings:

```text
| Area | Finding | Required action |
| --- | --- | --- |
| Java | Target Spring Boot requires Java N+ | update toolchain/CI/Docker |
| Test slices | package/module changed | update imports/dependencies |
| Jackson | namespace/default behavior changed | migrate imports/config/tests |
```

## PR Split Guidance

Choose the smallest split that reduces real risk.

Use a single PR for:

- patch upgrades in the same Spring Boot line
- minor upgrades with no toolchain jump and low dependency churn

Use two or more PRs for:

- Spring Boot major upgrades
- Java, Gradle, or Kotlin upgrades required before Spring Boot
- Jackson 2 to 3 migration
- Spring Security or Spring Kafka major changes
- large approval snapshot churn

Typical split:

```text
PR 1: Toolchain and current-major patch/minor baseline
PR 2: Deprecated API cleanup and dependency compatibility prep
PR 3: Spring Boot major upgrade and breaking-change fixes
PR 4: warning cleanup, snapshot updates, and follow-up simplification
```

## Implementation Workflow

### 1. Baseline Verification

Before editing, run the smallest useful baseline checks if the environment is available:

```bash
./gradlew test
./gradlew integrationTest -Dapprovaltests.quiet=true
```

For slow or environment-heavy projects, run targeted tests or compile first and record why the full suite was skipped.

### 2. Toolchain Prerequisites

Upgrade prerequisites before the Spring Boot major jump:

- Java toolchain and local version files
- Gradle or Maven wrapper
- Kotlin plugin and JVM target
- Docker base image
- CI `java-version`

After toolchain edits, run at least:

```bash
./gradlew clean build -x test
./gradlew test
```

### 3. Spring Boot Version Edit

For Gradle plugin projects, update:

```kotlin
plugins {
    id("org.springframework.boot") version "<target>"
    id("io.spring.dependency-management") version "<compatible>"
}
```

For Maven projects, update the Spring Boot parent or dependency management BOM.

Prefer Spring Boot BOM-managed versions over unnecessary explicit dependency versions.

### 4. Compatibility Dependency Edits

Adjust dependencies only when the target Spring Boot line requires it. Common examples:

- MyBatis Spring Boot Starter major version for Spring Boot major lines
- Flyway starter/module changes
- Spring Modulith BOM version
- Spring Cloud release train
- Spring Kafka and Spring Retry compatibility
- logstash-logback-encoder or logging stack compatibility
- explicit servlet/web/test modules split by the target Boot line

Do not add speculative dependencies. Tie each dependency change to a compatibility finding or compiler/test failure.

### 5. Source Migration

Use compile errors, migration guide findings, and focused searches to drive source changes.

Common migration patterns:

- `@MockBean` / `@SpyBean` to the replacement test annotations for the target Spring Boot line.
- Spring Boot test import/module changes for MVC, GraphQL, or web slices.
- RestTemplate/RestClient builder API changes.
- Spring Kafka annotation or retry API changes.
- Configuration property renames or removed properties.
- Removed deprecated APIs from the previous major line.

For Jackson 3 migrations:

- Move `com.fasterxml.jackson.core.*` and `com.fasterxml.jackson.databind.*` imports to `tools.jackson.*` where required.
- Keep `com.fasterxml.jackson.annotation.*` when the target stack still uses Jackson annotations from that namespace.
- Replace `JsonProcessingException` handling with the target Jackson exception type when the API changed.
- Rebuild `ObjectMapper` customizations using the target builder/module APIs.
- Explicitly pin behavior when Jackson 3 defaults differ from Jackson 2, especially null primitives, trailing tokens, enum string behavior, property ordering, date/time serialization, and unknown properties.
- Expect approval snapshot churn for JSON order or formatting changes; inspect diffs before approving.

### 6. Configuration Migration

Search configuration files for changed properties:

- `application.yml`, `application-*.yml`
- `application.properties`
- test resources
- Helm/Kubernetes values
- environment variable docs

Use migration guide and configuration changelog findings before renaming properties.

### 7. Verification Loop

Run checks in increasing scope:

```bash
./gradlew clean build -x test
./gradlew test
./gradlew integrationTest -Dapprovaltests.quiet=true
./gradlew check
```

Use Maven equivalents for Maven projects:

```bash
./mvnw test
./mvnw verify
```

When a check fails:

- Identify the first actionable failure.
- Decide whether it is an upgrade regression, existing baseline failure, test fixture drift, or environment issue.
- Fix and rerun the smallest failing check before broadening again.
- For ApprovalTests, inspect `.received.*` and `.approved.*`; do not approve snapshots unless the user asked or the behavior change is intentionally part of the upgrade.

## Regression Comparison

If failures are ambiguous, compare against the pre-upgrade branch:

```bash
git stash push -u -m spring-boot-upgrade-wip
git switch <baseline-branch>
./gradlew test
git switch -
git stash pop
```

Use a non-destructive workflow and preserve user changes. Do not reset or checkout away unrelated work.

## Review Checklist

Before finishing, check:

- Spring Boot version and dependency management are updated in exactly the intended places.
- Toolchain files agree with the required Java/Gradle/Kotlin versions.
- Explicit dependency versions are justified or removed in favor of the BOM.
- Migration guide breaking changes are either applied or documented as not applicable.
- Configuration property changes are covered.
- JSON serialization behavior is intentionally preserved or intentionally changed.
- Test changes are scoped to upgrade effects.
- CI, Docker, and local developer setup are not left inconsistent.

## Final Report

Report:

- version path taken
- changed files by category
- compatibility findings that drove dependency/source changes
- verification commands and pass/fail status
- remaining risks, especially runtime-only risks such as Kafka listener validation, security filters, database migration behavior, or JSON compatibility
- rollback plan for production-impacting upgrades

For PR descriptions, include:

```markdown
## Summary
- Spring Boot x.y.z -> a.b.c
- Related toolchain/dependency updates

## Migration Guide Findings
- Finding and action

## Verification
- [x] command and result

## Rollback
- Revert this PR / revert version line / redeploy previous image
```
