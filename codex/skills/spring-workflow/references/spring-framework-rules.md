# Spring Framework Rules

Use this reference for Java or Kotlin Spring planning, implementation, and review. These are structure and interface rules, so they take priority over local style preferences.

Apply explicit user decisions and narrower project rules first. Inspect nearby working use cases before choosing a structure; these defaults do not require converting an existing architecture.

## Service and API contracts

- Use verb-led use-case names such as `CreateOrder`, `FindOrders`, or `CancelPayment`.
- Where the project uses one endpoint class per use case, keep reads, creation, and cancellation in separate use-case classes. Follow that convention instead of introducing a generic `Controller` suffix or a service that only forwards calls.
- Separate a service when it owns meaningful application logic, serves multiple entry points, or follows a required project boundary; do not add a layer solely because Spring supports it.
- Prefer immutable request/response types: Java records where supported, or Kotlin data classes when their value semantics fit. Nest `Request` / `Response` types in their owning use case when appropriate; use named `XxxRequest` / `XxxResponse` types when shared across boundaries.
- Handle use-case failures at the owning controller boundary and return stable, descriptive error codes, such as `DELIVERY_NOT_FOUND`, rather than raw exception messages or opaque numeric codes. The frontend owns user-facing wording and localization. Use the controller's exception handler when appropriate; keep unexpected exception details in server logs.
- Preserve transaction rollback when converting exceptions into API errors. Do not swallow a failure inside a transaction and return a normal response that allows partial writes to commit.
- Follow established authentication and authorization boundaries. A project-specific choice to rely on menu permissions does not establish a general rule to remove backend authorization.

## Persisted and external codes

- Keep persisted or API enum codes independent from language-level constant names. Use an explicit `code` and an explicit conversion such as Java static `fromCode` or a Kotlin companion function; add a description where it helps readers understand the state.
- Check the actual database and JSON/GraphQL mappings: adding `code` does not help if persistence or serialization still uses `name()` or `valueOf()`.
- Handle unknown codes explicitly under the compatibility contract; do not silently turn an unknown state into success.

## Time handling

- Capture current time once at the execution boundary and pass it to time-dependent business decisions. Avoid multiple independent `now()` calls within one operation.
- Reuse an existing time parameter or clock. Inject `Clock` when controlling time materially improves verification; do not add a dedicated configuration class solely to introduce it.
- If the contract follows server time, use the server's configured zone (for example, `Clock.systemDefaultZone()`). Use a fixed business zone only when the contract requires it.
- A combined endpoint/use-case class may capture server time at entry. Do not require an otherwise unnecessary service split to satisfy time-handling style.
- Do not use SQL `NOW()` for business timestamps; bind application-provided time values instead.
- Preserve explicit execution-time parameters used for tests or emergency/manual runs unless the user changes that contract.

## Transactions and concurrency

- Do not introduce pessimistic locking when writing or changing queries. This includes `SELECT ... FOR UPDATE`, `SELECT ... FOR SHARE`, and equivalent ORM pessimistic-lock options. A concurrency concern alone does not authorize an exception to this rule.
- Identify the actual race and invariant, then use an appropriate alternative such as a conditional update with an affected-row check, optimistic version checking, or a unique constraint. Verify that the chosen approach preserves the required behavior; do not assume these alternatives are interchangeable.
- If the invariant cannot be maintained under this constraint, explain the concrete conflict instead of silently adding a pessimistic lock. Do not remove an existing lock mechanically without assessing its callers, transaction boundary, and replacement concurrency protection.
- Before adding a non-default isolation level, identify the concrete race, required invariant, and why the existing transaction or conditional write is insufficient.
- Reuse the project's transaction manager and persistence mechanism. Do not introduce a second database access approach when the existing one meets the need.

## Package structure

- Prefer package-by-feature over package-by-layer.
- Keep related controller, use-case, repository interface, domain type, and enum in the same feature package when that matches the existing project direction.
- In Java, use package-private visibility for implementation details where practical. Kotlin `internal` applies to the compilation module and does not enforce feature-package encapsulation. Use the project's module-boundary checks for those constraints.
- Deliberately expose boundary types needed by other features, including types in their signatures. Follow the project's API/SPI placement; do not impose a specific subpackage convention on every project.

## Dependency direction

- Use-case controllers own the input, response, and lookup contracts they need. Do not make their public responses depend on DTOs nested in a persistence Mapper, or make the use case depend directly on a SQL/MyBatis Mapper.
- Infrastructure adapters implement the use-case-owned contracts; persistence Mappers and their row types stay behind that boundary. The dependency points from infrastructure toward the higher-level contract.
- Reuse an existing suitable repository contract before introducing another interface. Do not introduce an interface for every class or a forwarding facade without a concrete boundary or substitution need.
- Domain code should remain independent from framework and infrastructure concerns where practical.

## Cross-package communication

- Prefer clear public interfaces or facades for package-to-package calls.
- Use events when looser coupling is the better fit.
- Avoid direct dependencies on another package's internal implementation classes.
- Avoid cyclic dependencies between feature packages.

## Review priorities

When reviewing or self-reviewing Java or Kotlin Spring changes, check these first:

1. Use-case structure that conflicts with the project, including forwarding-only layers
2. Boundary ownership of request/response records, error codes, and persisted enum codes
3. Inconsistent operation time or timezone semantics, and unnecessary clock infrastructure
4. Newly introduced pessimistic locking, unjustified isolation overrides, or parallel persistence mechanisms
5. New package-by-layer drift in code that should live under a feature package
6. Direct dependencies on `Jpa...`, `MySql...`, or other concrete infrastructure classes from high-level use cases
