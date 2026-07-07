# Milestone 30 — Background Job Framework

## Purpose

Sentinel now has ingestion, scans, behavior intelligence, anomaly detection, and case workflows. These should not all run synchronously from HTTP requests.

Milestone 30 introduces a background job framework scaffold.

## Added

- JobType
- JobStatus
- JobRequest
- JobRecord
- JobService
- JobHandler abstraction
- JobHandlerRegistry
- default no-op handlers
- API for enqueue/list/run
- tests

## API

```text
POST /api/v1/jobs
POST /api/v1/jobs/{job_id}/run
GET /api/v1/jobs
```

## Router registry update

Add this to `backend/app/platform/routing/router_registry.py`:

```python
from app.platform.jobs.api.routes import router as jobs_router

RouterDefinition(jobs_router, "/jobs", ["Jobs"])
```

## Current limitation

This milestone uses an in-memory repository and no-op handlers. The next milestone should add persistent job storage and real handlers for:

- Quartz sync
- scan run
- behavior refresh
- anomaly scoring
- anomaly case attachment
