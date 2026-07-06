# Backend-backed Timeline Retrieval API

Milestone 13 connects the frontend timeline visualization to backend data.

## Added

- normalized timeline activity persistence model
- Alembic migration
- timeline activity repository
- timeline API response mapper
- repository-backed `/api/v1/timelines/{login_session_external_id}` endpoint
- frontend API client for timeline retrieval
- dashboard timeline loading with demo fallback

## API response shape

```json
{
  "case_id": "LS-1001",
  "day_start": "2026-07-01T08:00:00+00:00",
  "day_end": "2026-07-01T18:00:00+00:00",
  "lanes": [],
  "evidence": []
}
```

## Design note

The endpoint is intentionally based on `login_session_external_id`, not internal database ID. Sentinel must remain connector-neutral.
