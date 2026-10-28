# Milestone 7 - Scan Orchestration and Investigation Case Management

## Purpose

Convert Sentinel from an on-demand analytics engine into an auditable investigation platform.

## Durable model

- `analysis_scans` records the analytical execution boundary.
- `durable_findings` stores immutable engine output with a canonical SHA-256 hash.
- `investigation_cases` stores mutable human workflow state.
- `case_findings` links immutable findings into one or more investigations.
- `investigation_audit_events` records case and scan actions.

Investigators must never edit `durable_findings`. If analytical logic changes, a new scan produces a new assessment version rather than mutating historical evidence.

## Workflow

OPEN -> IN_REVIEW -> AWAITING_INFO -> IN_REVIEW -> RESOLVED -> CLOSED

Direct OPEN -> CLOSED is permitted for clearly invalid/duplicate cases. CLOSED is terminal in the standard workflow.

Final dispositions include false positive, valid adjustment, policy violation, payroll correction and escalated.

## API

- POST `/api/v1/scans`
- GET `/api/v1/scans/{scan_id}`
- GET `/api/v1/scans/{scan_id}/findings`
- POST `/api/v1/investigations`
- GET `/api/v1/investigations/{case_id}`
- PATCH `/api/v1/investigations/{case_id}`
- GET `/api/v1/investigations/{case_id}/audit`

## Important limitation

The current milestone establishes durable orchestration records and investigation workflow. Heavy scan execution should run in Celery workers in the next production-hardening step rather than inside synchronous HTTP requests.
