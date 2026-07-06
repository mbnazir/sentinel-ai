# Milestone 24 — Explainable Anomaly Detection Engine

## Purpose

Milestone 24 adds explainable anomaly scoring over behavior features.

This is not a black-box ML model. It uses robust peer deviation scoring so investigators can understand why an entity is anomalous.

## Added

- FeatureVector model
- FeatureAnomaly model
- AnomalyScore model
- Robust median/MAD statistics
- Explainable anomaly scorer
- Behavior profile to feature-vector mapper
- API scaffold for anomaly scoring
- Tests

## API

```text
POST /api/v1/anomaly/score
```

Manually register this route in `backend/app/api/v1/router.py`:

```python
from app.anomaly.api.routes import router as anomaly_router

api_v1_router.include_router(
    anomaly_router,
    prefix="/anomaly",
    tags=["Anomaly Detection"],
)
```

## Why MAD instead of simple average?

Timekeeping and behavior data is skewed. Mean/stddev can be distorted by outliers. Median absolute deviation is more robust for fraud/integrity analytics.

## Next step

Wire anomaly scores back into the risk engine and persisted behavior profiles.
