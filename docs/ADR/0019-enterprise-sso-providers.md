# ADR-0019: Add enterprise SSO provider scaffolding

## Status

Accepted

## Context

Enterprise customers commonly use Azure AD / Entra ID, Google Workspace, Okta, or similar identity providers.

## Decision

Implement Azure AD and Google Workspace on top of a generic OIDC provider boundary.

## Consequences

- Sentinel can integrate with common enterprise IdPs.
- Provider-specific claim mapping remains isolated.
- The auth core remains provider-agnostic.
