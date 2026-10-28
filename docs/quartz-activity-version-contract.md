# Quartz activity version comparison contract

## Verified snapshot schema

`activity_snapshots` stores ingestion run ID, source system, source session ID, source activity ID, employee ID, `data_source_id`, activity type ID, interval timestamps, duration seconds, comment, Quartz created/updated timestamps, and metadata. `session_snapshots` stores session identity, employee, shift date, timestamps, and payroll/session statuses. There is no activity-to-session foreign key. The comparator associates records only with the full key `ingestion_run_id + source_system + source_session_id`, and verifies that the session belongs to the requested employee and payroll week before returning activity evidence.

The comparator reads one ingestion run and never joins source versions across runs. The existing unique constraints scope source activity IDs to an ingestion run and source system. This endpoint is read-only and writes no findings.

## Quartz data-source semantics

The local Quartz contract defines the following values as alternative representations/revisions of an activity timeline:

| ID | Source |
|---:|---|
| 0 | Phone |
| 1 | System |
| 2 | Agent Edited |
| 3 | Supervisor Edited |
| 4 | Manager Edited |
| 5 | Payroll Edited |

These timelines are compared pairwise and never added together. A source ID labels a representation; it does not identify the human editor or prove a complete chronological audit trail. A source 3 record does not establish that the assigned supervisor made the edit. Activity created/updated timestamps are retained as evidence and are not treated as authoritative edit timestamps.

The comparator does not assign descriptions to activity type IDs. Type changes are reported as ID transitions only.

## Comparison methodology

1. Convert timezone-aware timestamps to UTC. Naive timestamps are interpreted as UTC with a readiness warning.
2. Treat each valid activity interval as half-open `[start, end)`.
3. Use the sorted union of boundaries from both versions to form atomic segments.
4. On each segment compare the active type classifications from each version. Same classification is unchanged even if activity IDs differ; ID changes alone never create findings.
5. A one-sided interval is added/removed. A contiguous one-sided boundary adjacent to the same classification in both versions is extended/shortened. A different classification over shared coverage is reclassified.
6. Conflicting activity types overlapping within one version are ambiguous. Overlap uses set coverage, so duplicate/overlapping rows cannot increase measured elapsed time.
7. Coalesce adjacent segments only if change type, classifications, and activity evidence identities match.
8. Compare timestamp-derived duration with source `duration_seconds`; differences over one second are flagged. The timestamps define interval segmentation; source duration is not substituted into boundaries.
9. Missing end times and invalid intervals produce ambiguous evidence and prevent a complete net-coverage calculation. Missing source versions are incomplete.

`net_covered_seconds` measures only the difference between the two interval unions. `reclassified_seconds` measures the duration of shared coverage whose activity type differs; it is not added time or payable time. Fractional timestamp precision is preserved with decimal arithmetic. Evidence confidence is left unset rather than assigning an unsupported numeric score.

## WF-005 — Activity Reclassification Across Review Stages

WF-005 is a provisional review signal emitted only when at least one defensible interval is classified as `RECLASSIFIED`. It separates observation from interpretation and suspected risk. It does not claim fraud, editor identity, payroll eligibility, or financial impact. It is suppressed when an interval is malformed or either requested source version is missing.

### Regression example

Session `180596739`, agent-edited source 2 has one activity type 2 interval from 11:55:00 to 12:00:00 UTC (300 seconds, comment `bio`). Supervisor-edited source 3 has type 2 from 11:55:00 to 11:57:17 UTC (137 seconds, `edited`) and type 7 from 11:57:17 to 12:00:00 UTC (163 seconds, `OT Break`).

Expected comparison: 163 seconds reclassified from type 2 to type 7; net covered-time difference zero. Source creation timestamps are preserved, but editor identity and financial impact are `UNVERIFIED`. WF-005 is a review lead only; this is not overtime inflation or a fraud verdict.

## API and access

`GET /api/v1/weekly/{employee_id}/{day}/activity-changes?ingestion_run_id={uuid}&source_session_id={id}` compares source 2 to 3 by default. `original_source_id` and `revised_source_id` can select any distinct IDs 0–5. Existing role authentication applies. The query additionally binds the requested session to the supplied employee, ingestion run, Quartz source system, and payroll week; missing/mismatched sessions return 404 to avoid disclosing other employees' records. The repository currently has no tenant-to-employee ACL model; deployment requiring tenant-specific restrictions must add that authorization boundary before exposing this endpoint across tenants.

Example request:

```http
GET /api/v1/weekly/262513/2026-08-26/activity-changes?ingestion_run_id=00000000-0000-0000-0000-000000000001&source_session_id=180596739
Authorization: Bearer <viewer-or-investigator-token>
```

Response shape (abbreviated):

```json
{
  "employee_id": "262513",
  "session_id": "180596739",
  "ingestion_run_id": "00000000-0000-0000-0000-000000000001",
  "compared_versions": {"original": "quartz-source-2", "revised": "quartz-source-3"},
  "change_summary": {"change_count": 2, "reclassified_seconds": "163", "net_covered_seconds": "0"},
  "readiness": {"status": "READY", "reasons": []},
  "finding": {"code": "WF-005", "classification": "provisional_review_signal", "editor_identity": "UNVERIFIED", "financial_impact": "UNVERIFIED"},
  "editor_identity": "UNVERIFIED",
  "financial_impact": "UNVERIFIED"
}
```

## Known limits and required future contracts

- A pair of available versions is not proof that every intermediate review source was captured. The API compares only the requested pair and does not infer a full revision history.
- Actor identity requires a source audit event that identifies authenticated actor, action, target activity, before/after payload, and trusted event time. Assignment fields and source IDs are insufficient.
- Payable impact requires an authoritative Quartz contract for payable activity types, eligibility statuses, break rules, rounding, and payroll reconciliation. Activity type descriptions are not inferred here.
- Before/after version retention or a source-provided revision/correlation ID would improve split/merge correspondence. Current comparison reports interval facts without inventing record lineage.
- Tenant/user-specific employee access is not modeled by the existing auth layer; only role authentication and requested employee/session binding are enforced.
