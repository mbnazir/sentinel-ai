# ADR-0018: Provider-agnostic SSO

## Status

Accepted

## Context

Enterprise customers may use Azure AD, Google Workspace, Okta, or another identity provider.

## Decision

Implement SSO through a provider abstraction and map identity provider groups to Sentinel roles.

## Consequences

- Sentinel is not locked to one IdP.
- Tenant-specific group mapping can be added later.
- Security remains centralized through Principal and Role models.
