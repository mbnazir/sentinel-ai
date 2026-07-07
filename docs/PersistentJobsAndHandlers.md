# Milestone 31 — Persistent Jobs + Real Handlers

## Purpose

Milestone 30 introduced an in-memory/no-op job framework. Milestone 31 adds persistent job storage and real handlers for operational workflows.

## Added

- `job_runs` table
- persistent job repository
- persistent job API routes
- Quartz sync job handler
- scan run job handler
- anomaly case attachment job handler
- persistent job registry

## Router registry update

Replace the previous jobs router registration with:

```python
from app.platform.jobs.api.persistent_routes import router as persistent_jobs_router

RouterDefinition(persistent_jobs_router, "/jobs", ["Jobs"])
```

## Supported job payloads

### Quartz Sync

```json
{
  "job_type": "quartz_sync",
  "organization_id": "ORG1",
  "payload": {
    "shift_date_from": "2026-07-01",
    "shift_date_to": "2026-07-15"
  }
}
```

### Scan Run

```json
{
  "job_type": "scan_run",
  "organization_id": "ORG1",
  "payload": {
    "shift_date_from": "2026-07-01",
    "shift_date_to": "2026-07-15",
    "create_cases": true,
    "minimum_case_score": 61
  }
}
```

### Anomaly Case Attachment

```json
{
  "job_type": "anomaly_case_attachment",
  "organization_id": "ORG1",
  "payload": {
    "entity_type": "agent",
    "entity_id": "A1",
    "minimum_score": 61
  }
}
```

## Next milestone

Add scheduled jobs / recurring automation.
