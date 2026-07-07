# Automated Scan Pipeline

Milestone 21 adds the first true end-to-end scan workflow.

## Flow

```text
normalized_login_sessions
        |
        v
normalized_activities
        |
        v
TimelineBuilder
        |
        v
SourceMatchService
        |
        v
RuleEngine
        |
        v
RiskScorer
        |
        v
ScanSummary
```

## Endpoint

```text
POST /api/v1/scans/run
```

Payload:

```json
{
  "organization_id": "ORG1",
  "shift_date_from": "2026-07-01",
  "shift_date_to": "2026-07-15",
  "create_cases": true,
  "minimum_case_score": 61
}
```

## Current behavior

Milestone 21 scans normalized sessions and returns scored session results.

## Next improvement

Milestone 22 should create investigation cases automatically for sessions above the minimum case score and persist scan results.
