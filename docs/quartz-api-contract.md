# Quartz to Sentinel API Contract v1

Sentinel treats Quartz as read-only. Quartz should expose two paginated endpoints intended for controlled analytical extraction. The primary filter is `shift_date`; Sentinel does not request a single disputed session as its analytical boundary.

## Login Sessions

`GET /api/sentinel/v1/login-sessions`

Query parameters:
- `shift_date_from`: inclusive ISO date, required
- `shift_date_to`: inclusive ISO date, required
- `limit`: page size
- `cursor`: opaque continuation token

Each item should expose the relevant Quartz `login_sessions` columns without renaming them, including `id`, `agent_id`, `supervisor_id`, `shift_date`, `start_date`, `end_date`, dispute/status fields, workflow action timestamps, `ready_for_payroll`, `session_added_by`, `add_session_reason_id`, `payroll_adjusted`, `payroll_adjust_dt`, `multiple_logins`, agent/machine fields, and primary campaign/client fields.

## Activities

`GET /api/sentinel/v1/activities`

Query parameters:
- `login_session_ids`: comma-separated Quartz login session IDs, required
- `limit`: page size
- `cursor`: opaque continuation token

Each item should expose `activities.id`, `login_session_id`, `agent_id`, `data_source_id`, `activity_type_id`, `source_id`, `start_time`, `end_time`, `duration`, `inactivity_time`, campaign/client fields, `comment`, `created_at`, `updated_at`, and `computer_merged`.

## Data Source Semantics

- 0: Phone
- 1: System
- 2: Agent
- 3: Supervisor
- 4: Manager
- 5: Payroll

Sentinel rejects unknown source IDs rather than silently misclassifying them.

## Pagination Envelope

Preferred response:

```json
{
  "items": [],
  "next_cursor": null
}
```

The cursor must be opaque and stable for the lifetime of the extraction. Sentinel also accepts a plain JSON array for non-paginated development endpoints.

## Security

Use service-to-service authentication, TLS, least-privilege authorization, request throttling, and API audit logging. The Sentinel connector record must never contain a bearer token or password.


## Optional organizational enrichment (Milestone 6)
For organizational analytics, login-session responses should additionally expose `manager_id`, `site_id`, `site_name`, and `team_id` as-of the requested shift date when Quartz can resolve them authoritatively. Do not send current hierarchy as historical hierarchy unless that semantic is explicitly documented.
