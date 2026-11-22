---
name: legacy-feature-extension-review
description: Review additions to an existing batch, integration, or operational feature for regressions in the original path, transaction boundaries, external side effects, and user-visible behavior. Use when extending a live workflow with reservations, new states, or an optional processing path; not for standalone style review or greenfield design.
---

# Legacy Feature Extension Review

Review the extension against the existing behavior and the user's agreed changes. Stay read-only unless fixes are requested. Review approval does not authorize deployment, production data writes, or external retransmission.

## Establish the unchanged contract

- Read the diff, the original execution path, its callers, and relevant configuration. Use source history to distinguish existing behavior from the proposed addition.
- Record the few invariants that matter: aggregation semantics, selection dates, identifiers, file naming/content, schedule timezone, and manual execution behavior. Check only those affected by the change.
- Identify explicit decisions and accepted limitations. Do not silently replace them with stronger locking, additional states, new tables, or a different delivery guarantee.
- Inspect the existing persistence and UI patterns before proposing new dependencies or components. Reuse compatible mechanisms, not an obsolete feature merely because its name is similar.

## Check the original and extended paths

- With no new records, does the original path still produce the same business result? Identify intentional changes, such as rollback on upload failure, separately.
- When new records become eligible, do they join the existing aggregation exactly as agreed? Do not assume accumulation means addition; inspect the actual query and grouping keys.
- Check eligibility boundaries, cutoff equality, retries, cancellation, and date rollover where the extension introduces them. Preserve the explicit execution time used by tests or emergency runs.
- Trace how a new-path failure affects the original path. If continuation is required, verify that the failed write is contained and the transaction remains usable. Do not add savepoints or recovery layers without a concrete requirement.

## Trace writes, reads, and external side effects

Follow one eligible record through selection, registration, aggregate read, file generation, external transfer, and completion recording when those steps exist.

- Inspect the actual transaction manager, datasource, connection/session sharing, propagation, and async boundaries. An annotation alone does not prove the transaction covers the whole flow.
- For write-then-read, verify the read uses the same transaction and writer connection, or another explicitly valid visibility strategy. Check replica routing and caches instead of assuming commit timing is sufficient.
- An external upload is not rolled back by a database transaction. Verify the required direction: upload failure must propagate or mark rollback so covered DB writes do not commit, and completion must follow confirmed upload success.
- Check thrown failures and false/no-op results separately. A caught exception or skipped transfer must not become a successful completion accidentally.
- Preserve accepted failure limitations, such as upload success followed by DB commit failure. Report a material unmet guarantee; do not introduce distributed transaction machinery for a risk the user explicitly accepted.
- Require a demonstrated invariant before recommending explicit row locks or isolation overrides. A no-lock requirement does not eliminate the database's normal write locks.

## Check status and administrative UI contracts

Apply this section only when the extension affects an API or screen.

- Separate persisted/internal states from display labels. Verify the API-to-UI mapping, filters, and actions for each state that can actually occur.
- Existing records without reliable status evidence should remain unknown/blank according to the agreed UX. Do not label them complete merely because they predate the new table.
- Follow the application's established table pattern: density, row ordering, fixed viewport region, and scrolling. When mobile use is required, verify horizontal overflow and reachable controls without losing the desktop layout.
- Enforce business cutoffs on the server and recheck them in the UI before submission, including dialogs left open past the deadline. Browser time is not authoritative.
- Follow the established error-code/message and authentication/authorization contracts. Menu visibility alone is not a general substitute for backend authorization.

## Verify the risk, not the implementation shape

For Java/Kotlin/Spring changes, use the shared [static-check and review boundary](../java-spring-workflow/references/jvm-review-checks.md). Keep configured diagnostic results separate from business and runtime-contract findings. Passing formatting or architecture checks does not establish transaction or delivery correctness.

Select a small set of scenarios that distinguishes a correct extension from a regression: no new records, eligible and not-yet-eligible records, successful external transfer, and failed transfer with expected database state. Add only applicable boundary or retry cases.

- Use existing tests and fixtures first; add missing business or integration coverage when fixes are requested and project rules require it.
- Assert observable outcomes such as generated rows/file content and committed or rolled-back state. Avoid tests that only mirror private methods, mocks, or platform defaults.
- A real integration check of application-specific MyBatis/JDBC transaction sharing or writer routing can be necessary even though the framework itself is tested elsewhere.
- Distinguish maintained regression tests from temporary probes. A request to remove implementation-time tests is scoped to that task, not a standing prohibition on tests.
- Do not manually trigger a production batch or retransmit a file just to verify a code change without explicit authorization. Use local evidence or authorized read-only runtime evidence.

## Report

Lead with confirmed defects, each with `file:line`, the triggering scenario, the observed behavior, and the smallest correction. Distinguish verified behavior, untested paths, and accepted limitations. If there are no findings, state what was checked rather than claiming all regressions are impossible.
