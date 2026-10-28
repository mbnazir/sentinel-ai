# Quartz REST Connector

The Quartz connector is read-only and emits Sentinel normalized contracts. Its primary extraction boundary is an inclusive `shift_date` range; it never assumes one `login_session` equals one employee day.

Expected Quartz endpoints:

- `GET /api/sentinel/v1/login-sessions?shift_date_from=YYYY-MM-DD&shift_date_to=YYYY-MM-DD&limit=N&cursor=...`
- `GET /api/sentinel/v1/activities?login_session_ids=1,2,3&limit=N&cursor=...`

Response envelope may be either a JSON array or `{ "items": [...], "next_cursor": "..." }`.

Authentication credentials are not persisted in the connector record. Milestone 2 uses the `QUARTZ_API_BEARER_TOKEN` process secret; a secrets-provider abstraction will replace that in production hardening.
