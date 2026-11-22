---
name: java-spring-workflow
description: "Use after an approved plan when implementing or revising Java/Spring code. This skill applies the repository's Java/Spring rules, performs a self-review loop, fixes clear violations, and verifies the result."
---

# Java/Spring Implementation Workflow

Use this skill for Java or Spring implementation work after the design is already settled.

Do not use this skill during brainstorming. Prefer it when the user already has an approved plan or a concrete Java/Spring implementation request and wants rule-aware execution with a self-review loop.

## Quick Start

1. Confirm the task is actually Java/Spring work.
2. Read the approved plan or the user's concrete implementation request.
3. Read the canonical references:
   - `references/spring-framework-rules.md`
   - `references/java-code-style.md`
4. Implement the smallest viable change.
5. Run a dedicated Java/Spring self-review on the diff.
6. Fix clear rule violations.
7. Run diagnostics, tests, and build checks that matter for the change.

## When To Use

- Implementing a Spring feature after planning is complete
- Revising Java/Spring code to align with repository rules
- Performing "implement, self-review, fix, verify" loops on Java/Spring changes

## When Not To Use

- Brainstorming or open-ended design exploration
- Non-Java work
- Generic code review without implementation

## Workflow

### 1. Confirm scope

Look for Java/Spring signals such as:

- `pom.xml` or `build.gradle(.kts)`
- `src/main/java`
- Spring annotations like `@Service`, `@RestController`, `@Repository`

If the task is not Java/Spring work, say so plainly and fall back to the normal implementation path instead of forcing this skill.

### 2. Load the right context

Read the approved plan first. Then load the references:

- Always read `references/spring-framework-rules.md`
- Read `references/java-code-style.md` when changing Java source

Treat the approved plan and the user's later corrections as the source of truth for what to build. Apply explicit user decisions and narrower project conventions before the reference defaults.

### 3. Implement with plan-level rules first

During implementation, prioritize the rules that affect structure and interfaces:

- use-case classes use verb-led names and follow the project's endpoint structure without forwarding-only layers
- use-case-local request/response types are inner records; shared boundary types follow `XxxRequest` / `XxxResponse`
- current time is captured once at the boundary using the existing time parameter or clock strategy
- persisted enum codes and API error codes follow explicit contracts rather than incidental Java names or user-facing text
- explicit locks and isolation overrides need a demonstrated concurrency requirement
- package-by-feature is preferred over package-by-layer
- high-level code depends on interfaces, not concrete infrastructure classes

Do not bloat the diff chasing every style issue in untouched legacy code. Keep the scope tight to the requested change and the code you necessarily touch.

### 4. Run a Java/Spring self-review pass

Before final verification, review the changed files against both references. Check at minimum:

- use-case naming and unnecessary controller/service forwarding
- request/response ownership, error-code mapping, and persisted enum-code conversion
- consistent operation time and timezone semantics, including `LocalDateTime.now()` and SQL `NOW()` usage
- justification for explicit locks, isolation overrides, and new persistence mechanisms
- composed methods at a single abstraction level, business-intent names, and readable layout
- package structure drift toward layer-based organization
- concrete implementation dependencies in high-level code
- accessor naming (`xxx()` over `getXxx()`)
- unnecessary `@Builder`
- `final` usage, logging consistency, and other local Java style rules

Fix clear violations before concluding.

### 5. Verify

Run the smallest relevant verification set that gives real confidence:

- diagnostics on modified files
- targeted tests
- build or compile checks when applicable

Do not claim completion without verification evidence.

Select tests by the behavior they protect. Check existing coverage first, preserve required fail-first workflows, and add missing coverage for business rules or demonstrated regressions. Prefer assertions on observable outcomes over assertions that merely repeat method calls, implementation details, or framework behavior.

Integration checks for this application's transaction wiring, database routing, or rollback boundaries are meaningful when those are the risk; they are not redundant just because Spring or MyBatis supplies the underlying mechanism. Keep temporary diagnostic probes separate from maintained tests. Do not delete useful tests merely because they were introduced during implementation, and do not generalize a task-specific deletion request into a ban on tests.

## Reporting

In the final response, include:

- what was implemented
- what Java/Spring rule issues were found and fixed in the self-review loop
- what verification was run
- any remaining intentional exceptions or risks
