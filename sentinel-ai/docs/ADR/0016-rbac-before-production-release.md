# ADR-0016: RBAC before production release

## Status

Accepted

## Context

Sentinel AI handles sensitive workforce integrity data. Production use without role-based access control would be irresponsible.

## Decision

Introduce RBAC and security hardening before production release.

## Consequences

- APIs can begin enforcing permissions.
- Frontend can attach bearer tokens.
- Production SSO can be integrated without changing domain logic.
