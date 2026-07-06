# Persist Normalized Quartz Ingestion

Milestone 20 persists Quartz API ingestion into Sentinel-owned normalized stores.

## Added

- normalized login session model
- normalized activity model
- Alembic migration
- idempotent normalized ingestion repository
- persisted Quartz ingestion service
- sync API now persists fetched data

## Updated endpoint

```text
POST /api/v1/connectors/quartz/sync
```

Payload:

```json
{
  "organization_id": "ORG1",
  "shift_date_from": "2026-07-01",
  "shift_date_to": "2026-07-15"
}
```

Response:

```json
{
  "fetched_sessions": 100,
  "fetched_activities": 800,
  "persisted_sessions": 100,
  "persisted_activities": 800
}
```

## Why this matters

The connector no longer only fetches data. It now writes into Sentinel's normalized operational store, enabling downstream timeline reconstruction, matching, rules, and behavior analytics without repeatedly calling Quartz.
