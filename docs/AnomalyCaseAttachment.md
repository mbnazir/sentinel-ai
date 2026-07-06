# Milestone 27 — Anomaly Case Attachment

## Purpose

Persisted anomaly findings are useful, but investigators work in cases. Milestone 27 attaches anomaly evidence to investigation cases.

## Added

- anomaly case evidence builder
- anomaly case attachment service
- duplicate open-case reuse
- anomaly attach-case API
- tests

## API

```text
POST /api/v1/anomaly-cases/attach-case
```

Payload:

```json
{
  "organization_id": "ORG1",
  "entity_type": "agent",
  "entity_id": "A1",
  "minimum_score": 61
}
```

Manually register route:

```python
from app.anomaly.api.case_routes import router as anomaly_case_router

api_v1_router.include_router(
    anomaly_case_router,
    prefix="/anomaly-cases",
    tags=["Anomaly Cases"],
)
```

## Design

The service first looks for an existing open investigation case for the same entity. If found, it appends anomaly evidence. If not, it creates a new case.
