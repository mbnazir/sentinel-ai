# Enterprise SSO + Persistent User Management

Milestone 17 introduces persistent user management and SSO scaffolding.

## Added

- `sentinel_users` table
- user domain model
- user repository
- local user creation
- local login
- SSO profile model
- SSO provider abstraction
- mock SSO provider
- SSO role mapper
- SSO auth service
- user API
- SSO API

## SSO strategy

The SSO architecture is provider-agnostic.

Future providers:

- Azure AD / Entra ID
- Google Workspace
- Okta
- Ping Identity

## Current endpoints

```text
POST /api/v1/users
POST /api/v1/users/login
POST /api/v1/sso/mock/callback
```

## Warning

The mock SSO provider is development-only.
