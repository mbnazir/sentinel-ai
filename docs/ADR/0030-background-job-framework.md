# ADR-0030: Background jobs before scheduled automation

## Status

Accepted

## Context

Long-running ingestion and scan workflows should not block request/response APIs.

## Decision

Introduce a job framework with handler abstraction before adding scheduled automation.

## Consequences

- Workflows can be queued and executed consistently.
- Scheduler and worker implementations can be added later.
- The HTTP API becomes an orchestration layer, not the execution engine.
