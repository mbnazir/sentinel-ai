# ADR-0017: Enforce route permissions and audit workflow actions

## Status

Accepted

## Context

RBAC without route enforcement is cosmetic. Investigation actions must also be auditable.

## Decision

Apply permission dependencies to workflow routes and emit audit events from workflow actions.

## Consequences

- Sensitive operations require appropriate permissions.
- Case lifecycle changes become traceable.
- Future compliance reports can use audit logs.
