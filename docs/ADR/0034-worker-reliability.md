# ADR-0034: Add reliability primitives before production worker execution

## Status

Accepted

## Context

Workers executing fraud scans and ingestion jobs need operational safety.

## Decision

Introduce retry, dead-letter, heartbeat, and lease primitives before wiring them into worker execution.

## Consequences

- Failure behavior becomes explicit.
- Duplicate job execution can be prevented.
- Future worker observability has clear data structures.
