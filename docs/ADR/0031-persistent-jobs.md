# ADR-0031: Persistent jobs and real handlers

## Status

Accepted

## Context

In-memory jobs are useful for local testing but not production operations.

## Decision

Persist job records and add real handlers for core workflows.

## Consequences

- Job history is auditable.
- Long-running workflows become trackable.
- A scheduler/worker can execute the same job service.
