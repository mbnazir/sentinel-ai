# ADR-0036: Domain event bus

## Status

Accepted

## Context

Direct orchestration between ingestion, scans, behavior intelligence, anomaly detection, case creation, and notifications creates tight coupling.

## Decision

Introduce persisted domain events and an in-process event bus.

## Consequences

- Workflows can be decoupled.
- Events are auditable and replayable later.
- Future subscribers can trigger jobs, notifications, and AI summaries.
