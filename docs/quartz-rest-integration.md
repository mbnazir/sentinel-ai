# Connecting Sentinel AI to Quartz REST

Sentinel never writes to Quartz. Quartz is the source system; Sentinel consumes read-only REST endpoints and stores immutable snapshots in its own PostgreSQL database.

## Required Quartz endpoints

Default connector contract:

```text
GET /api/sentinel/v1/login-sessions
GET /api/sentinel/v1/activities
```

The endpoint paths can be changed in Sentinel connector configuration.

## Authentication

Recommended:

```http
Authorization: Bearer <read-only-service-token>
```

Use a dedicated service identity that can only read the Sentinel export endpoints.

Set the same token in Sentinel:

```env
QUARTZ_API_BEARER_TOKEN=<read-only-service-token>
```

Do not store this token in the Sentinel `connectors` table.

## 1. Login sessions endpoint

Request:

```http
GET /api/sentinel/v1/login-sessions
    ?shift_date_from=2026-08-24
    &shift_date_to=2026-08-26
    &limit=500
    &cursor=<optional>
```

Minimum required fields:

```json
{
  "id": 177001234,
  "agent_id": 306412,
  "shift_date": "2026-08-26",
  "start_date": "2026-08-26T08:00:00+00:00"
}
```

Strongly recommended full payload:

```json
{
  "id": 177001234,
  "agent_id": 306412,
  "supervisor_id": 41001,
  "manager_id": 51001,
  "site_id": "PK-LHE",
  "site_name": "Lahore",
  "team_id": "TEAM-14",
  "shift_date": "2026-08-26",
  "start_date": "2026-08-26T08:00:00+00:00",
  "end_date": "2026-08-26T17:00:00+00:00",
  "status_id": 3,
  "dispute_reason_id": 5,
  "dispute_state": 2,
  "supervisor_status_id": 1,
  "ready_for_payroll": 1,
  "payroll_adjusted": 0,
  "payroll_adjust_dt": null,
  "session_added_by": null,
  "add_session_reason_id": null,
  "agent_action_timestamp": "2026-08-26T17:10:00+00:00",
  "supervisor_action_timestamp": "2026-08-26T17:35:00+00:00",
  "manager_action_timestamp": null,
  "multiple_logins": 0,
  "agent_ip": "10.0.0.10",
  "machine_hostname": "LHE-PC-001",
  "primary_campaign_id": "WMT",
  "primary_campaign_name": "Walmart",
  "primary_client_id": 44,
  "primary_client_name": "Walmart",
  "data_source_id": 1,
  "session_source": 1,
  "resolve_dispute_by": 41001,
  "closed_by": 41001,
  "closed_by_type": 1,
  "overtime": 0,
  "regular_hour": 8
}
```

Response should be either a raw array or a paged object. Paged form is preferred:

```json
{
  "items": [
    { "...": "..." }
  ],
  "next_cursor": "177001234"
}
```

If there is no more data:

```json
{
  "items": [],
  "next_cursor": null
}
```

### Important query rule

Filter by:

```sql
login_sessions.shift_date
```

not by `created_at`, because Sentinel analysis is defined around the employee's shift date.

A single agent can have multiple `login_sessions` for the same `shift_date`. Return all of them. Never collapse them.

## 2. Activities endpoint

Request:

```http
GET /api/sentinel/v1/activities
    ?login_session_ids=177001234,177001235,177001236
    &limit=500
    &cursor=<optional>
```

Required payload:

```json
{
  "id": 3921400001,
  "login_session_id": 177001234,
  "agent_id": 306412,
  "data_source_id": 1,
  "activity_type_id": 10,
  "source_id": 4,
  "start_time": "2026-08-26T08:00:00+00:00",
  "end_time": "2026-08-26T09:00:00+00:00",
  "duration": 3600,
  "inactivity_time": 0,
  "campaign_id": "WMT",
  "campaign_name": "Walmart",
  "client_id": 44,
  "comment": null,
  "created_at": "2026-08-26T08:00:01+00:00",
  "updated_at": null,
  "computer_merged": 0
}
```

Sentinel understands these Quartz `data_source_id` values:

```text
0 = Phone
1 = System
2 = Agent
3 = Supervisor
4 = Manager
5 = Payroll
```

Any other value is rejected by the Quartz connector rather than silently misclassified.

## Recommended Quartz indexes

The existing indexes on:

```text
login_sessions.shift_date
activities.login_session_id
activities.data_source_id
```

are important.

For the export endpoint, the key access path should be:

```text
login_sessions:
shift_date -> id / agent_id

activities:
login_session_id -> data_source_id -> start_time
```

Do not create large unbounded REST queries against Quartz.

## Quartz pagination

Use keyset pagination rather than OFFSET for large tables.

Example concept for sessions:

```sql
WHERE shift_date BETWEEN :from AND :to
  AND id > :cursor
ORDER BY id
LIMIT :limit
```

Return the last `id` as `next_cursor`.

Activities:

```sql
WHERE login_session_id IN (...)
  AND id > :cursor
ORDER BY id
LIMIT :limit
```

## Test Quartz directly before involving Sentinel

Sessions:

```bash
curl -H "Authorization: Bearer $QUARTZ_TOKEN" \
  "https://quartz.example.internal/api/sentinel/v1/login-sessions?shift_date_from=2026-08-26&shift_date_to=2026-08-26&limit=2"
```

Activities:

```bash
curl -H "Authorization: Bearer $QUARTZ_TOKEN" \
  "https://quartz.example.internal/api/sentinel/v1/activities?login_session_ids=177001234&limit=10"
```

Confirm JSON timestamps are ISO-8601 and include timezone/offset.

## Register Quartz in Sentinel

```bash
curl -X POST http://localhost:8000/api/v1/connectors \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quartz Production Read Only",
    "connector_type": "quartz",
    "mode": "rest-api",
    "enabled": true,
    "base_url": "https://quartz.example.internal",
    "config": {
      "sessions_path": "/api/sentinel/v1/login-sessions",
      "activities_path": "/api/sentinel/v1/activities",
      "timeout_seconds": 30,
      "page_size": 500,
      "verify_tls": true
    }
  }'
```

Save the returned connector `id`.

## Test the Sentinel -> Quartz connection

```bash
curl -X POST \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  http://localhost:8000/api/v1/connectors/<CONNECTOR_ID>/test
```

Expected:

```json
{"connected": true}
```

## Import Quartz data

Start small. Use one shift date first:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion-runs \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connector_id": "<CONNECTOR_ID>",
    "shift_date_from": "2026-08-26",
    "shift_date_to": "2026-08-26",
    "idempotency_key": "quartz-20260826-test-001"
  }'
```

The response returns:

```text
id
session_count
activity_count
status
```

Save the ingestion `id`.

## Run the integrity scan

```bash
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ingestion_run_id": "<INGESTION_RUN_ID>",
    "date_from": "2026-08-26",
    "date_to": "2026-08-26",
    "requested_by": "babar.local",
    "scope": "employee_day"
  }'
```

Milestone 13 automatically queues the scan to Celery.

Poll:

```bash
curl \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  http://localhost:8000/api/v1/scans/<SCAN_ID>
```

When status becomes `completed`, read findings:

```bash
curl \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  http://localhost:8000/api/v1/scans/<SCAN_ID>/findings
```

Or open:

```text
http://localhost:8080
```

## One-command assisted E2E run

After generating a Sentinel token:

```bash
python scripts/run_quartz_e2e.py \
  --token "$SENTINEL_TOKEN" \
  --quartz-url "https://quartz.example.internal" \
  --from-date 2026-08-26 \
  --to-date 2026-08-26
```

The script:

1. Registers Quartz.
2. Tests connectivity.
3. Imports immutable sessions/activities.
4. Starts a background scan.
5. Polls completion.
6. Prints the first findings.

## First UAT recommendation

Do not begin with 90 days.

Use:

1. One known normal shift date.
2. One known legitimate dispute.
3. One shift where Agent changed time.
4. One Supervisor-adjusted shift.
5. One Manager-adjusted shift.
6. One Payroll-adjusted shift.
7. Then expand to 3 days.
8. Then one payroll period.
9. Only then run 30/60/90-day behavioral analysis.

This is necessary to calibrate false positives before management sees aggregate risk scores.
