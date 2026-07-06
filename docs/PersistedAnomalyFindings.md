# Milestone 26 — Persisted Anomaly Findings

## Purpose

Milestone 25 integrated anomaly results into the risk model, but anomaly outputs were still transient. Milestone 26 persists anomaly findings so they can be used by dashboards, investigations, and audit trails.

## Added

- `anomaly_findings` persistence model
- Alembic migration
- `AnomalyFindingRepository`
- `AnomalyPersistenceService`
- anomaly findings retrieval API
- tests

## API

```text
GET /api/v1/anomaly-persistence/findings?organization_id=ORG1&entity_type=agent
```

Manually register this route in `backend/app/api/v1/router.py`:

```python
from app.anomaly.api.persistence_routes import router as anomaly_persistence_router

api_v1_router.include_router(
    anomaly_persistence_router,
    prefix="/anomaly-persistence",
    tags=["Anomaly Persistence"],
)
```

## Next step

Attach persisted anomaly findings to investigation cases automatically.
