# ADR-0037: Emit domain events from workflows

## Status

Accepted

## Context

A domain event bus is only useful if core workflows emit events.

## Decision

Add event emission wrappers for jobs and investigation case changes.

## Consequences

- Workflow chaining becomes possible without hard-coded service dependencies.
- Events become an audit and replay mechanism.
- Job handlers can trigger downstream processing safely.
