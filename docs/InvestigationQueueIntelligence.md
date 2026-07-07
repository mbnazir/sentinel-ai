# Milestone 28 — Investigation Queue Intelligence

## Purpose

Cases are not all equal. Investigators need an operational queue that combines risk, SLA urgency, assignment state, and age.

## Added

- investigation SLA policy
- queue scoring service
- queue item model
- queue summary model
- investigation queue service
- queue API
- tests

## API

```text
GET /api/v1/investigation-queue?organization_id=ORG1
```

Manually register:

```python
from app.investigations.queue.api_routes import router as investigation_queue_router

api_v1_router.include_router(
    investigation_queue_router,
    prefix="/investigation-queue",
    tags=["Investigation Queue"],
)
```

## Queue score

Queue score combines:

- risk score
- priority
- unassigned status
- SLA breach / SLA due soon
- case age

## Why this matters

Risk score says how suspicious a case is. Queue score says what investigators should work first.
