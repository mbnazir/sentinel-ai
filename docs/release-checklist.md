# Sentinel AI Release Candidate Checklist

## Security
- Enterprise SSO/OIDC configured
- Group-to-role mapping reviewed
- Secrets externalized
- TLS termination configured
- CORS restricted to approved origin
- Security headers verified
- Dependency and SAST scans clean or formally accepted

## Data and Quartz
- Quartz REST contract verified in staging
- TLS certificate chain validated
- Read-only Quartz service identity used
- Pagination and 429/5xx retry tested
- Source API rate limits documented
- No write permission to Quartz

## Reliability
- PostgreSQL backup/restore drill passed
- Redis restart recovery passed
- Celery worker-loss recovery passed
- Stale chunk recovery tested
- Dead-letter procedure documented
- Scan cancellation tested

## Compliance UAT
- Known legitimate adjustment produces expected evidence
- Agent-only edit scenario detected
- Supervisor-added time scenario detected
- Manager-added time scenario detected
- Payroll-added time scenario detected
- Repeated multi-shift behavior detected
- False-positive disposition retained in audit history
- Evidence hash remains stable
