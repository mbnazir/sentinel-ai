# Quartz API Production Connector

Milestone 19 hardens the Quartz connector from scaffold to production-shaped ingestion.

## Added

- Quartz API client
- retry-aware request wrapper
- paginated session fetch
- batch activity fetch
- DTO mapper
- normalized mapper
- ingestion service
- shift-date range sync API
- environment variables
- connector tests

## Endpoint

```text
POST /api/v1/connectors/quartz/sync
```

Payload:

```json
{
  "shift_date_from": "2026-07-01",
  "shift_date_to": "2026-07-15"
}
```

## Expected Quartz API contract

```text
GET /api/sessions
POST /api/activities/batch
```

The actual Quartz API paths can be adapted in `QuartzAPIClient`.

## Important

The connector is API-first. Direct database access should remain a fallback only.
