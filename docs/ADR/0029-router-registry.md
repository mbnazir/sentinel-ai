# ADR-0029: Use centralized router registry

## Status

Accepted

## Context

As the platform grew, `backend/app/api/v1/router.py` became a merge conflict hotspot.

## Decision

Use a centralized router registry and keep `router.py` minimal.

## Consequences

- Fewer merge conflicts.
- Route registration is auditable.
- Tests can validate duplicate route prefixes.
- Feature modules become easier to add safely.
