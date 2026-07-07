# Route-level Permission Enforcement and Audit Logging

Milestone 16 enforces the RBAC model introduced in Milestone 15.

## Added

- route-level permission dependencies on workflow APIs
- persistent audit log repository
- persistent audit log service
- investigation workflow audit events
- tests for permission expectations and audit event structure

## Protected workflow permissions

| Endpoint behavior | Required permission |
|---|---|
| list cases | view_cases |
| assign case | assign_cases |
| transition case | manage_cases |
| add comment | manage_cases |
| generate narrative | generate_ai_narrative |

## Audit events

- investigation.case_created
- investigation.case_assigned
- investigation.case_transitioned
- investigation.comment_added
- investigation.narrative_generated

## Important

This is still not full production authentication. It enforces bearer-token permissions but does not yet implement enterprise SSO or persistent user management.
