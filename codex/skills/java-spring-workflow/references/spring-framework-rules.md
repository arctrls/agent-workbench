# Spring Framework Rules

Use this reference for Java/Spring planning, implementation, and review. These are structure and interface rules, so they take priority over local style preferences.

Apply explicit user decisions and narrower project rules first. Inspect nearby working use cases before choosing a structure; these defaults do not require converting an existing architecture.

## Service and API contracts

- Use verb-led use-case names such as `CreateOrder`, `FindOrders`, or `CancelPayment`.
- Where the project uses one endpoint class per use case, keep reads, creation, and cancellation in separate use-case classes. Follow that convention instead of introducing a generic `Controller` suffix or a service that only forwards calls.
- Separate a service when it owns meaningful application logic, serves multiple entry points, or follows a required project boundary; do not add a layer solely because Spring supports it.
- Prefer immutable request/response records. Use inner `Request` / `Response` records when they belong to one use case; use named `XxxRequest` / `XxxResponse` types when shared across boundaries.
- Follow the project's error contract. Where the frontend owns user-facing wording, return stable error codes through the endpoint's exception handler and map them to messages in the frontend.
- Follow established authentication and authorization boundaries. A project-specific choice to rely on menu permissions does not establish a general rule to remove backend authorization.

## Persisted and external codes

- Keep persisted or API enum codes independent from Java constant names. Use an explicit `code` and a static conversion method such as `fromCode`; add a description where it helps readers understand the state.
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

- Before adding explicit row locks or a non-default isolation level, identify the concrete race, required invariant, and why the existing transaction or conditional write is insufficient.
- Honor an explicit no-lock requirement; do not add `FOR UPDATE` or equivalent protection speculatively. Report a demonstrated correctness conflict instead of silently changing the agreed design.
- Reuse the project's transaction manager and persistence mechanism. Do not introduce a second database access approach when the existing one meets the need.

## Package structure

- Prefer package-by-feature over package-by-layer.
- Keep related controller, use-case, repository interface, domain type, and enum in the same feature package when that matches the existing project direction.
- Default internal implementation classes to package-private.
- Expose `public` types only when another package genuinely needs them.

## Dependency direction

- High-level use cases should depend on interfaces, not concrete infrastructure classes.
- The client package should own the interface it needs.
- Infrastructure classes implement those interfaces.
- Domain code should remain independent from framework and infrastructure concerns where practical.

## Cross-package communication

- Prefer clear public interfaces or facades for package-to-package calls.
- Use events when looser coupling is the better fit.
- Avoid direct dependencies on another package's internal implementation classes.
- Avoid cyclic dependencies between feature packages.

## Review priorities

When reviewing or self-reviewing Java/Spring changes, check these first:

1. Use-case structure that conflicts with the project, including forwarding-only layers
2. Boundary ownership of request/response records, error codes, and persisted enum codes
3. Inconsistent operation time or timezone semantics, and unnecessary clock infrastructure
4. Speculative row locks, isolation overrides, or parallel persistence mechanisms
5. New package-by-layer drift in code that should live under a feature package
6. Direct dependencies on `Jpa...`, `MySql...`, or other concrete infrastructure classes from high-level use cases
