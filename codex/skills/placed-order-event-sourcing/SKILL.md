---
name: placed-order-event-sourcing
description: Use for Pacman repository work that creates, reviews, or refactors PlacedOrder event-sourced paths, including updateOrder, admin order changes, projection writer changes, event appliers, feature-flagged event-sourcing migrations, characterization tests for order projections, and decisions about domain logic versus application-service side effects.
---

# PlacedOrder Event Sourcing

## Core Rules

- Identify orders by `PlacedOrder`, not by projection tables such as `SELL` or
  `SELL_GOODS`.
- Treat "order" as the fingerprint-covered order rows. Those values belong to
  events and the projection writer.
- Treat current stock, goods data, sequences, ledgers, stock deduction, and
  redistribution as external inputs or side effects.
- Keep appliers pure. Do not read databases, call services, allocate sequences,
  access clocks, or execute actions from an applier.
- Put side effects in the application service. It may gather external inputs,
  validate preorders, allocate sequence values, and execute stock/ledger writes.
- Put domain calculations in `postorder/placedorder` domain types where possible:
  line changes, shipment line changes, shipment status, order distribution, and
  price/distribution calculations.
- Keep `ActionSet`, action rows, and projection rows out of pure domain seams.
  Use them only in the original path or at an application-service adapter edge.
- Event payload values are changes, not current snapshots. Do not add redundant
  `delta` naming just to restate that.
- Keep the original path minimally changed, especially feature-flag-off behavior.

## Required Starting Point

Before implementing a new event-sourced path, first pin behavior with
characterization tests.

- Use order creation through the event-sourced path to create varied
  `PlacedOrder` fixtures.
- Cover combinations that affect projection rows, not only the happy path.
- Snapshot or otherwise verify projection rows before relying on a refactor.
- Add feature-flag-on tests for the use case under migration. Feature-flag-off
  tests only prove the original path still works.
- Include any order-adjacent side effect that the use case truly owns, such as
  stock redistribution or ledgers. If the original path does not do it, call that
  out as a policy change rather than a regression.

Projection checks should usually include:

- `SELL`
- `SELL_ADD`
- `SELL_GOODS`
- `SELL_DELIY_ADDR`
- `SELL_DELIY_ADDR_GOODS`
- `SELL_DELIY_ADDR_ADD`

## Parallel Investigation

Use parallel `explorer` subagents when the task spans at least two of these
surfaces: the original path, the event-sourced path, or characterization-test
coverage. Keep small, isolated lookups in the main agent.

Spawn these three read-only investigations with the target use case and known
entry point in every brief:

1. **Original-path explorer**
   - Trace the feature-flag-off path from its entry point through `ActionSet`
     actions and external side effects.
   - Identify which fingerprint-covered rows change and which stock, ledger,
     sequence, or redistribution effects actually occur.
2. **Event-path explorer**
   - Trace the feature-flag-on path through the application service, event,
     applier, and projection writer.
   - Identify event payload values, domain calculations, external inputs, and
     every projection row written.
3. **Coverage explorer**
   - Find characterization and integration tests, fixtures, feature-flag
     coverage, and assertions for the affected projection rows and side effects.
   - Report missing coverage without creating or editing tests.

Require every explorer to return:

- relevant file paths and symbols
- the traced flow in execution order
- observed behavior separated from assumptions
- unresolved questions or contradictory evidence

Explorers must not edit files, choose the domain design, or recommend unrelated
cleanup. Wait for all requested investigations, reconcile disagreements against
the source, and verify material delegated claims before editing.

The main agent owns the combined change map and all domain decisions. Use
exactly one writer—the main agent or one implementation worker—for source and
test changes. Never let parallel agents edit the same worktree.

## Workflow

1. Run the parallel investigation when the task meets its delegation threshold;
   otherwise inspect the relevant path directly.
2. Reconcile the original path, event-sourced path, and coverage findings into
   one evidence-backed change map.
3. List fingerprint-covered order rows and non-order external side effects.
4. Check whether each side effect exists in the original path before requiring it
   in the new path.
5. Add or extend characterization tests for feature-flag-on behavior.
6. Gather external inputs in the application service.
7. Move pure calculations into `postorder/placedorder` domain code.
8. Build event payloads as changes.
9. Apply events with pure appliers.
10. Write fingerprint-covered projection rows through the projection writer.
11. Execute external side effects from the application service.
12. When the diff is substantial, ask two read-only `explorer` subagents to
    review it independently: one checks domain-boundary invariants and the
    other checks projection/test coverage.
13. Review their evidence, fix confirmed findings with the single writer, and run
    the required verification commands in the main agent.

## Review Checklist

- `PlacedOrder` is the order identity source.
- The application service does not smuggle projection rows into domain seams.
- Domain code has no repository, action service, sequence, or clock dependency.
- Appliers are stateless and deterministic.
- New event values are changes.
- Projection writer updates every fingerprint-covered order row the use case
  changes.
- Feature-flag-on tests verify the new event path directly.
- Feature-flag-off tests still pass for the original path.
- Verification includes `./gradlew testClasses` and the focused integration or
  characterization tests.
