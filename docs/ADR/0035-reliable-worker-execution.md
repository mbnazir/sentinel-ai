# ADR-0035: Wire reliability primitives into worker execution

## Status

Accepted

## Context

Reliability primitives are useless unless the worker execution path uses them.

## Decision

Introduce a reliable worker path using leases, heartbeat, and ReliableJobRunner.

## Consequences

- Worker execution becomes safer for production.
- Duplicate execution risk is reduced.
- Retry/DLQ semantics are centralized.
