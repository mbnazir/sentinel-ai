# Security Hardening and RBAC

Milestone 15 introduces the first enterprise security controls.

## Added

- role model
- permission model
- principal model
- authorization service
- JWT token service
- password hashing service
- FastAPI auth dependencies
- development token endpoint
- security headers middleware
- audit log service scaffold
- frontend auth header injection

## Roles

- admin
- compliance
- investigator
- supervisor
- read_only

## Important

`/api/v1/security/dev-token` is for local development only. Production must replace it with real authentication such as:

- Azure AD
- Google Workspace
- Okta
- internal SSO

## Security headers

The API now adds:

- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy

## Next hardening items

- persistent users/roles
- login endpoint backed by users table
- refresh tokens
- audit log persistence
- route-level permission enforcement across all workflow endpoints
- rate limiting
- tenant isolation checks
