# Milestone 32 — Scheduled Job Automation

## Purpose

Persistent jobs are useful, but operations need recurrence. Milestone 32 adds schedule definitions and due-job enqueueing.

## Added

- job schedule model
- job schedule migration
- schedule calculator
- schedule repository
- scheduler service
- scheduler API
- tests

## API

```text
POST /api/v1/schedules
GET /api/v1/schedules
POST /api/v1/schedules/run-due
```

## Router registry update

Add this to `backend/app/platform/routing/router_registry.py`:

```python
from app.platform.scheduler.api.routes import router as scheduler_router

RouterDefinition(scheduler_router, "/schedules", ["Schedules"])
```

## Example

```json
{
  "name": "Daily Quartz Scan",
  "organization_id": "ORG1",
  "job_type": "scan_run",
  "frequency": "daily",
  "payload": {
    "shift_date_from": "2026-07-01",
    "shift_date_to": "2026-07-01"
  },
  "created_by": "admin"
}
```

## Next milestone

Add a worker process / scheduler runner that calls `run-due` continuously or via cron/Kubernetes CronJob.
