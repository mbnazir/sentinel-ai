# Milestone 12 - Enterprise Security, Quartz Integration and Release Candidate

Sentinel RC establishes API authentication/RBAC, hardened JWT validation, security headers, constrained CORS, production API/worker/frontend containers, Quartz transient-failure retry behavior, and secure environment templates.

Roles:
- viewer: read analytics/dashboard
- investigator: read analytics and operate investigations
- manager: investigator capability plus ingestion
- admin: full platform and connector administration

Important: the included JWT mechanism is the application authorization boundary. Enterprise SSO still requires deployment-specific federation (for example Entra ID/OIDC through an identity-aware proxy or direct OIDC validation). Do not expose the RC externally using locally minted tokens as the enterprise login experience.

Release gates before production:
1. Configure enterprise IdP and group-to-role mapping.
2. Store database/JWT/Quartz credentials in an approved secret manager.
3. Execute migrations against staging PostgreSQL.
4. Validate Redis/Celery worker recovery.
5. Run frontend npm production build in CI.
6. Run anonymized Quartz end-to-end UAT.
7. Load test representative payroll-period volume.
8. Validate backup and restore.
9. Security review and dependency/SAST scan.
10. Compliance sign-off on rule interpretation and case dispositions.
