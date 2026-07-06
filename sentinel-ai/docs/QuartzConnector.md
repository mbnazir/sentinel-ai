# Quartz Connector

The Quartz connector is the first Sentinel AI integration.

## Preferred integration

Quartz REST APIs.

## Legacy integration

Read-only direct MySQL access may be added later for environments where APIs are not available.

## Required API contract

### GET /login-sessions

Query parameters:

- shift_date_from
- shift_date_to

Returns login sessions for all agents over the requested shift-date range.

### POST /activities/by-login-sessions

Request:

```json
{
  "login_session_ids": ["177075701", "177075702"]
}
```

Returns activities for those login sessions.

## Source mapping

| Quartz data_source_id | Sentinel source |
|---:|---|
| 0 | phone |
| 1 | system |
| 2 | agent |
| 3 | supervisor |
| 4 | manager |
| 5 | payroll |

## Design rule

Quartz fields are mapped into Sentinel domain entities before persistence. No rule engine logic may consume raw Quartz payloads directly.
