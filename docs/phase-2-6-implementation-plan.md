# Phase 2.6 Implementation Plan

This plan is gated on Quartz business-contract and security decisions. It does not authorize payroll calculation based on current provisional metadata.

## Priority 0 — Protect evidence and access

1. Obtain a Quartz read-only data dictionary and supported audit/payroll APIs from the Quartz owner. Confirm tenant boundaries, database/table ownership and whether access is authorized for Sentinel.
2. Establish a trusted principal → tenant → client/employee authorization source. Do not treat the request's `employee_id`, `primary_client_id`, or a role claim by itself as authorization. Ensure an investigator can access only the cases/populations they are granted.
3. Add an immutable access-audit event for allowed and denied reads of payroll/activity comparison evidence: authenticated principal, role, tenant, employee, session, ingestion run, endpoint, purpose/case reference, outcome, timestamp and correlation ID. Exclude tokens and unnecessary payroll values.
4. Apply non-enumerating 404 behavior, rate limits and monitored failed access. Restrict sensitive activity-change access to the least-privilege investigation roles until fine-grained policy is enforced.

## Priority 1 — Validate activity and payroll semantics

1. Receive the effective-dated activity type dictionary and eligibility matrix, including conditional rules by client/campaign/site/country/employee group.
2. Confirm whether timestamp intervals, stored `duration`, activity metadata, or a separate payroll calculation is authoritative. Define timezone, fractional precision, overlap, breaks, rounding and cross-midnight handling.
3. Confirm `regular_hour` and `overtime` units, precision, rounding, scope, finality, zero/missing semantics, precedence and payroll adjustment behavior.
4. Confirm weekly policy population and threshold(s), including policy effective date and workweek boundaries. Replace the unconditional Sentinel 40-hour constant with an explicit, reviewed policy object only after evidence arrives.
5. Reconcile representative Quartz payroll outputs against immutable input activity/session rows using Quartz-owned examples, including the supplied 163-second type reclassification. Do not treat comments as type semantics.

## Priority 2 — Add verified audit attribution

1. Integrate Quartz's documented immutable audit feed/history API; require actor principal, role-at-action, event ID/time, exact target interval lineage and before/after payload.
2. Preserve each returned event and its source cursor/version under a separately audited ingestion identity. Define pagination, coverage, retries, idempotency, retention and event-order guarantees.
3. Correlate activity versions to audit events by stable Quartz IDs, not timestamps or assigned supervisor fields. Mark unlinked or conflicting events unverified.
4. Add synthetic contract tests and controlled Quartz contract tests. Keep WF-005 a provisional review observation; do not produce fraud or monetary findings from type reclassification alone.

## Priority 3 — Ingestion and readiness

1. Add per-date/per-page checkpoints with atomic event/snapshot persistence or a safe replay/upsert policy. Record successful-empty dates distinctly from extraction failures.
2. Persist Quartz expected/received session and activity counts (and manifest identity) per date; only mark a range complete after exact reconciliation and all pages succeed.
3. Quarantine the existing failed, single-date-dominated run from weekly readiness. Verify its status, actual snapshot date distribution, and committed counts with read-only queries before any further analysis.
4. Run one bounded payroll week through a new isolated run after semantics/checkpointing are validated. Do not merge the 17,600 reported snapshots with other runs.

## Priority 4 — Payroll calculation readiness

Only after priorities 1–3 are signed off, implement baseline/final eligible seconds using the authoritative source and effective policy; deduplicate overlaps and source revisions; calculate incremental regular/overtime separately; retain exact provenance and rounding. Require complete reconciled week coverage and reliable original-vs-final evidence before calling impact verified. No individual financial responsibility is assigned without a documented attribution method.

## Read-only Quartz requests to unblock work

Ask the Quartz administrator for:

- supported API paths and sanitized schemas for activity type dictionary, payroll details/calculation, audit/history events, and expected-count manifests;
- catalog discovery results from `information_schema.columns` for `%activity%type%`, `%payroll%`, `%audit%`, `%history%`, and `%dispute%` relations;
- type descriptions and effective-dated payable eligibility policy;
- unit/precision/rounding and reconciliation examples for `regular_hour`, `overtime`, `duration`, payroll adjustment values;
- actor/action/target/before-after event history for approved sample session `180596739` and its intersecting source-2/source-3 interval;
- workflow/status/dispute enum values and state transitions; and
- tenant/client/employee access contract and API authorization model.

Use read-only credentials and sanitized outputs. Do not ask for broad production extracts when a small, approved sample and aggregate counts answer the question.
