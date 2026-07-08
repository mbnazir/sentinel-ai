# ADR-0014: Backend-backed timeline before advanced investigation UI

## Status

Accepted

## Context

The dashboard previously used demo timeline data. Advanced investigation UI must be grounded in backend data.

## Decision

Add repository-backed timeline retrieval before adding more UI controls.

## Consequences

- Timeline visualization can consume real normalized activities.
- Demo fallback remains available for local development.
- Future rule evidence can deep-link into timeline activities.
