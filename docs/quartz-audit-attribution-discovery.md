# Quartz Audit and Editor Attribution Discovery

## Executive finding

Sentinel does not currently have evidence to verify who changed an activity interval. Quartz source 2–5 identifiers denote alternative representations/stages; neither they nor assigned supervisor/manager IDs prove the human editor. Session action timestamps and activity created/updated timestamps are temporal context, not an authenticated, interval-specific audit event. **Editor attribution is not currently defensible.**

The documented Sentinel export contract lists only login-session and activity endpoints. It does not describe a separate audit/history endpoint. That does not prove Quartz lacks one; the authoritative Quartz code/schema and administrator access were unavailable.

## Supplied Phase 2.5 evidence

The prior-phase report identifies employee `314163`, shift date `2026-08-26`, session `180596739`, and ingestion run `a62525d0-3d22-4944-a4f3-5cc1540854f7`. Its source-2/source-3 comparison observed a 163-second interval classification change from activity type ID 2 to ID 7 with zero net covered-time difference. The supplied comment `OT Break` remains only the stored comment; it does not establish the payroll classification of type 7. The comparison is WF-005 provisional, with editor identity and financial impact unverified. These are supplied prior-phase results, not independently re-read from the failed run during this discovery phase.

## Evidence register

| Field / mechanism | Source | Verified meaning and supporting evidence | Confidence / classification | Payroll suitability | Fraud attribution suitability | Validation needed |
|---|---|---|---|---|---|---|
| `data_source_id` 2–5 | `app/domain/data_sources.py`; `docs/quartz-api-contract.md`; user-provided Quartz semantics | Labels agent, supervisor, manager, payroll representation. These are version sources, not named actors. | High for label mapping — VERIFIED | Not additive and not payroll eligibility. | Not sufficient to identify an editor. | Quartz must document generation/precedence semantics. |
| `supervisor_id`, `manager_id` | `_normalize_session`; session snapshot columns | Assigned organizational identities. The connector maps these separately from edits. | High — VERIFIED | No. | Not proof of the editor. | As-of assignment history and actor-vs-assignment semantics. |
| Session `closed_by`, `closed_by_type`, `resolve_dispute_by` | `_normalize_session` copies raw non-null values into `metadata_json` | Actor-like fields are preserved, but ID namespace, `closed_by_type` code meaning, and whether these correspond to activity edits are undocumented. | High raw preservation; LOW interpretation — UNKNOWN | Not payroll calculations. | Not verified attribution. | Data dictionary, authentication principal linkage, action scope and lifecycle. |
| `session_added_by` | Normalized first-class field and `session_snapshots.session_added_by` | Actor-like field for session addition. It is not documented as the author of later activity changes. | Medium — INFERRED | No. | May support a session-add event only after validating actor semantics; not interval edit attribution. | Quartz definition and audit event linkage. |
| `agent_action_timestamp`, `supervisor_action_timestamp`, `manager_action_timestamp` | Mapped to session timestamp columns | Action timing is retained at session level. No action ID, target activity ID, actor identity, before/after payload, or exact time edit linkage accompanies these fields. | High mapping; UNKNOWN correlation — INFERRED | No. | Insufficient alone. | Correlation IDs/event IDs tying action to exact interval/version and authenticated actor. |
| Activity `created_at`, `updated_at` | Maps to `source_created_at`, `source_updated_at` | Source timestamps are preserved. Their semantics (record creation vs edit time, timezone, actor association, backfill behavior) are not defined by local docs. | High mapping; UNKNOWN semantics — UNKNOWN | No. | Not sufficient to infer who changed a record or when the interval changed. | Quartz event contract and immutability/audit behavior. |
| Activity IDs and type/interval differences | `activity_snapshots`; `weekly/activity_comparison.py` | Version-aware comparison reports observed interval/type differences between selected representations. IDs identify rows; ID changes alone do not establish a modification. | High — VERIFIED | Net interval coverage is not payable amount. | Supports an observation, not an actor. WF-005 is provisional. | Source version lineage/correlation ID and a complete audit chain. |
| Before/after values | No before/after activity payload or audit field in `NormalizedActivity`/snapshot schema | The current export gives rows for different sources; it does not explicitly give old/new fields or a linked mutation event. Interval comparison can produce an observed difference, not a source-certified edit transaction. | High — VERIFIED absence in current contract; source-side availability UNKNOWN | Cannot reconstruct a verified payable baseline. | No action-level attribution. | Quartz audit/event history with exact target ID, before/after values and authenticated actor. |
| Approval/rejection workflow | `status_id`, `dispute_state`, `supervisor_status_id`, `dispute_reason_id` are integer fields | Numeric workflow context is persisted, but labels, transitions, actor, approval/rejection semantics, and relation to activity versions are undocumented. | UNKNOWN | Cannot infer approval or payable finality. | Cannot identify an approver from an assigned supervisor or status value. | Enumerations, state machine, event actor, timestamps, transition history. |
| Separate audit/history APIs/tables | Local `docs/quartz-api-contract.md` defines two export endpoints only | No audit endpoint or audit schema is described locally. Search found no Quartz server implementation in Sentinel. | UNKNOWN | n/a | n/a | Quartz administrator to identify history tables, CDC/audit service, or API. |
| Multiple edits in one stage | Source snapshots retain activity rows keyed by activity IDs and source stage | The documented contract does not specify version IDs, edit sequence IDs, or whether multiple same-stage revisions are retained. A single ingestion captures a point-in-time response. | UNKNOWN | No. | Cannot assert full edit sequence. | Confirm retention/version model and event ordering guarantees. |

## Exact interval attribution requirements

To claim a verified editor for a particular classification/time change, Quartz must expose a durable event with at least:

1. authenticated actor principal and immutable actor ID;
2. actor type/role at action time, independently distinguished from assigned supervisor/manager;
3. action ID, action timestamp with timezone and server authority, and event sequence/version;
4. target session ID and exact activity ID or stable interval lineage ID;
5. source state and target state, including before/after activity type, boundaries, duration and relevant metadata;
6. explicit action semantics (edit, approval, rejection, payroll override, reversal);
7. source-stage transition and indication whether the event is final, superseded, or rolled back; and
8. retention/coverage guarantees and pagination or reconciliation metadata.

Creation timestamps are not a substitute for an edit event. Assigned supervisor identity and source stage are never used as a fallback actor.

## Read-only Quartz administrator requests

First enumerate audit/history relations and their columns:

```sql
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
  AND (table_name ILIKE '%audit%'
       OR table_name ILIKE '%history%'
       OR table_name ILIKE '%activity%log%'
       OR table_name ILIKE '%dispute%')
ORDER BY table_schema, table_name, ordinal_position;
```

Ask the administrator to identify documented read-only APIs for audit events and revision history. If available, request a sanitized event chain for session `180596739`, limited to the source-2/source-3 activities intersecting `2026-08-25 11:55:00–12:00:00 UTC`, including actor principal, action, before/after type/bounds, event ID, and event timestamp. Do not infer actor identity from the example's `Supervisor Edited` label or its comment.

For approval workflow semantics, request the status/dispute code dictionary and event transitions for that session, including whether `closed_by`, `closed_by_type`, and `resolve_dispute_by` refer to a human actor, assigned reviewer, resolver, or final closer.
