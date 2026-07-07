# ADR-0038: Event-driven job runtime

## Status

Accepted

## Context

Event-emitting wrappers existed, but production execution still needed a runtime path that uses them.

## Decision

Introduce an event-aware job service and worker runtime.

## Consequences

- Job completion emits domain events.
- Workflow chaining can be event-driven.
- Future notifications and AI summaries can subscribe to events.
