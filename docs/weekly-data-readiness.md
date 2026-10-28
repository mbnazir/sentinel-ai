# Weekly payroll engine: Phase 2 data readiness

## Readiness decision

Weekly financial impact remains **provisional**. Quartz `regular_hour` and `overtime` are copied into session metadata without unit conversion. Repository examples show `regular_hour: 8` next to a nine-hour elapsed session, which makes hours a candidate unit; the implementation request describes observed values as seconds-like, sometimes fractional. Neither is a semantic contract. Sentinel does not convert either field or equate elapsed session time with payable time.

The repository has no authoritative baseline reconstruction or source count reconciliation. A successful extraction covering the entire week is consequently `UNVERIFIED`, not `COMPLETE`. Failed, queued, running, missing, or out-of-range runs are `INCOMPLETE`. “No session on a date” means no employee session was observed in that run; it does not prove missing Quartz data or prove a non-workday.

## Quartz field provenance

| Field | Observed mapping | Interpretation / limitation |
|---|---|---|
| `regular_hour`, `overtime` | Preserved as non-null values in session `metadata_json` | No conversion, precision contract, or authoritative-source rule. Candidate unit hours from docs; seconds reported in the target payload remain unverified. |
| Session `data_source_id`, `session_source` | Preserved in session metadata | Meaning/precedence not defined in the local contract. |
| `closed_by`, `closed_by_type`, `resolve_dispute_by` | Preserved in session metadata | Actor-like fields, but ID/type semantics and whether these identify the time editor are undocumented. |
| Activity `data_source_id` | Required integer 0–5, stored in activity snapshot | Describes representation/source (Phone, System, Agent, Supervisor, Manager, Payroll); not proof of the person who edited it. |
| Activity timestamps | Start/end mapped directly; integer `duration_seconds` computed from their difference; raw Quartz `duration` retained as `metadata.quartz_duration`; creation/update timestamps mapped | Elapsed activity time is analytical evidence, not payable time. |
| Session start/end | `start_date` / `end_date` mapped to normalized start/end timestamps | Elapsed session duration cannot be used as payable duration without policy evidence. |
| Supervisor/manager action times | `supervisor_action_timestamp` / `manager_action_timestamp` mapped to session action timestamp fields | They show action timing, not necessarily the action content or editor identity. |
| Assigned supervisor/manager | `supervisor_id` / `manager_id` mapped independently | Assignment does not establish who performed an adjustment. |

The local docs contain a sample session for `agent_id: 306412`, but there is no field coverage, null/zero distribution, activity-source distribution, run-date coverage, or reconciled count dataset in the repository. Docker daemon access was denied in this execution environment, and no local snapshot for employee `262513` / session `180702246` was found. Therefore the specific reason that this session has nonzero elapsed duration but zero regular/overtime metadata is **unresolved**. The connector retains source zeros; possible policy/status/serialization explanations cannot be distinguished from available evidence.

## Profile required when read-only database access is available

Run these aggregate queries against a read-only role and export counts only. Do not expose employee-level rows or credentials. Include filters by ingestion run and date range, and compare all returned counts with Quartz source-side counts. The current schema can report observed snapshots and metadata null/zero distributions, but Quartz expected counts and per-date successful-empty markers are not stored.

```sql
SELECT r.id, r.shift_date_from, r.shift_date_to, r.status,
       r.session_count, r.activity_count, r.started_at, r.completed_at
FROM ingestion_runs r
ORDER BY r.started_at DESC;

SELECT count(*) AS sessions,
       count(*) FILTER (WHERE metadata_json ? 'regular_hour') AS regular_present,
       count(*) FILTER (WHERE metadata_json->>'regular_hour' IS NULL) AS regular_null,
       count(*) FILTER (WHERE metadata_json->>'regular_hour' IN ('0','0.0')) AS regular_zero,
       count(*) FILTER (WHERE metadata_json ? 'overtime') AS overtime_present,
       count(*) FILTER (WHERE metadata_json->>'overtime' IN ('0','0.0')) AS overtime_zero,
       count(*) FILTER (WHERE metadata_json ? 'closed_by') AS closed_by_present,
       count(*) FILTER (WHERE metadata_json ? 'resolve_dispute_by') AS resolver_present
FROM session_snapshots WHERE ingestion_run_id = :run_id;

SELECT data_source_id, count(*) AS activities,
       count(*) FILTER (WHERE source_updated_at IS NOT NULL) AS updated_timestamp_present
FROM activity_snapshots WHERE ingestion_run_id = :run_id
GROUP BY data_source_id ORDER BY data_source_id;

SELECT shift_date, count(*) AS sessions
FROM session_snapshots WHERE ingestion_run_id = :run_id
GROUP BY shift_date ORDER BY shift_date;
```

Compare actual per-date and total session/activity counts with a Quartz export manifest. The current API/connector contract defines no expected source counts, so SQL counts alone cannot mark source coverage verified.

## Safe bounded ingestion for August 23–29, 2026

The connector accepts an inclusive shift-date range of up to 32 days; seven dates fit one run. Once the target dates are available, create exactly one run for `2026-08-23` through `2026-08-29`, omit `max_sessions`, and use a stable idempotency key that identifies connector and range. Poll `GET /api/v1/ingestion-runs/{run_id}` and retain that UUID for every inspection and analysis. Do not merge snapshots from separate runs.

The current workflow is **not safely resumable**: each batch commits, but failed runs restart from the beginning and there is no cursor/checkpoint. Unique `(ingestion_run_id, source_system, source_*_id)` constraints can make a replay fail on already persisted batches. Also `max_sessions` truncation may still end with status `completed`; never use it for readiness. Do not retry a failed run in place. Record the failed run and its counts, diagnose it, then create an isolated fresh run with a new idempotency key; keep both runs separate. This prevents duplicate mixing but does not make interrupted pulls resumable.

Before interpreting the week, require a successful run, all seven dates in range, no worker error, no test cap, and a Quartz-side manifest with expected sessions and activities per date matching the ingested run counts. Until Quartz supplies that manifest and the app stores/reconciles it, status stays `UNVERIFIED` and financial impact stays provisional. An employee having no shift on a date is distinct from the source endpoint successfully returning zero sessions for that date; current ingestion does not preserve that distinction.

## Business-rule blockers

1. Are `regular_hour` and `overtime` decimal hours, seconds, or another representation, and what precision/rounding applies?
2. Which Quartz source/version is authoritative when sources 0–5 differ, and are these values session totals, activity totals, or payroll-approved totals?
3. Which statuses make time eligible for pay, and can Quartz supply original/before values to reconstruct a baseline?
4. What do `closed_by`, `closed_by_type`, and `resolve_dispute_by` identify? Can Quartz expose immutable editor identity, action type, and before/after values?
5. Can the export provide expected record counts or explicit successful-empty coverage per date?
6. How should overlapping sessions, breaks, and cross-midnight intervals affect payable time under the client payroll policy?
