# Quartz Payroll Contract Discovery

**Scope:** repository and locally available connector-contract review only. This is documentation discovery, not authorization to calculate or persist payroll values. No Quartz source or PostgreSQL data was modified.

## Executive finding

Sentinel can observe session metadata containing `regular_hour`, `overtime`, payroll status flags, action timestamps, and Quartz activity intervals. It cannot establish which activity types are payable, the units of the two payroll metadata values, authoritative baseline/final rules, or the employee population and policy to which the 40-hour threshold applies. The current weekly payable resolver labels the values provisional and assumes seconds for internal representation; this is an implementation placeholder, not a validated Quartz contract. **Payable-time calculations are not currently defensible.**

The only local Quartz routes documented are paginated login-session and activity exports. No activity-type dictionary, payroll calculation, payroll detail/reconciliation, or policy API is documented. The sample payload in the local integration guide is illustrative and is not a field-level contract.

## Evidence register

| Field / rule | Source | Verified meaning and supporting evidence | Confidence / classification | Payroll suitability | Attribution suitability | Validation needed |
|---|---|---|---|---|---|---|
| Session `shift_date` | `app/connectors/quartz/rest.py::_normalize_session`; `docs/quartz-api-contract.md` | Maps Quartz `shift_date`; connector explicitly treats it as the business shift date instead of deriving from `start_date`. | High — VERIFIED | Suitable as the grouping date, not as payable duration evidence. | Not actor evidence. | Quartz to confirm effective timezone/calendar and cross-midnight policy. |
| Session `start_date`, `end_date` | Connector normalization to `start_at`, `end_at`; `session_snapshots` | Direct timestamp mapping. Sentinel can calculate elapsed session time but must not equate it with payable time. | High — VERIFIED | Elapsed context only. | Not editor identity. | Clarify timestamp timezone, corrections, overnight allocation. |
| `regular_hour`, `overtime` | Connector preserves non-null raw values in session `metadata`; stored in `session_snapshots.metadata_json`; local guide sample shows `8` and `0` | No unit conversion, Decimal/rounding contract, definition, source precedence, or authority is provided. A sample with `8` is compatible with hours but cannot establish units; prior payload reports seconds-like values. | High that fields are preserved; LOW on meaning — UNKNOWN | No. Do not use as verified payable seconds or money. | No. | Quartz data dictionary, units, precision, rounding, total-vs-component meaning, authoritative status and sample reconciliation. |
| Session `data_source_id`, `session_source` | Connector copies to `metadata_json` | Raw values preserved only. Local docs do not define session-level precedence. | Medium — UNKNOWN semantics | No until definitions are supplied. | No. | Enumerations and precedence rules. |
| `ready_for_payroll` | Connector maps to normalized boolean and `session_snapshots.ready_for_payroll` | Quartz readiness flag is observed; no local definition of what “ready” guarantees. | High mapping; LOW semantics — INFERRED | Not enough to establish paid/eligible time. | No. | State machine and finality/rollback semantics. |
| `payroll_adjusted`, `payroll_adjust_dt` | Mapped to `payroll_adjusted`, `payroll_adjusted_at` | Adjustment indicator and timestamp are observed; no adjustment amount, before/after detail, or adjustment reason contract. | High mapping; LOW effect — INFERRED | Not enough to reconstruct or value an adjustment. | Timestamp alone does not identify an editor or exact activity. | Payroll adjustment ledger/adjustment IDs and lifecycle semantics. |
| `status_id`, `dispute_state`, `supervisor_status_id`, `dispute_reason_id` | Normalized into integer session columns | Numeric workflow/status values are retained. No enum dictionary or transition contract found. | High mapping; UNKNOWN meaning | No eligibility inference. | At most workflow context; no actor proof. | Status dictionaries, approver action semantics, state transitions, effective dates. |
| Activity `activity_type_id` | Required integer in `NormalizedActivity`; stored on `activity_snapshots` | ID is preserved, but the repository has no activity type catalogue or description mapping. Type 2 and type 7 in the regression case are only IDs. | High mapping; UNKNOWN meaning | No. | Activity-classification evidence only. | Authoritative type dictionary, effective dates, policy conditions, code ownership. |
| Payable activity types and policy | No local field, API, table, or rule implementing a Quartz eligibility matrix | No source establishes paid/unpaid/break/training/conditional treatment, or variation by client, campaign, site, country, employee, or date. `OT Break` is a comment only. | UNKNOWN | No. | No. | Eligibility matrix and historical policy versioning from Quartz/payroll owner. |
| Activity `start_time`, `end_time` | `rest.py::_normalize_activity`; stored as `start_at`, `end_at` | Timestamps are parsed. Sentinel derives an integer duration from timestamp difference when an end exists. | High — VERIFIED | Potential interval evidence only; not proof of payable time. | Shows version boundary evidence, not the author/editor. | Confirm timezone, fractional precision, and whether boundaries are authoritative for timekeeping/payroll. |
| Activity `duration` | Connector retains source value as `metadata.quartz_duration`; normalized `duration_seconds` is derived from timestamps | Quartz `duration` can be a display string (connector comment example `0h 3m 32s`); local REST guide also gives numeric `3600`. Sentinel does not parse the raw field as payroll duration. Derived seconds use `int(total_seconds())`, truncating subsecond precision. | High mapping; UNKNOWN field semantics | Not suitable as payroll input without contract. | No. | Confirm endpoint type/units, rounding, whether stored duration can differ from endpoints. |
| `inactivity_time` | Mapped into `inactivity_seconds`, defaulting absent/falsy values to zero | Raw integer-ish inactivity is stored as seconds by field name/code, but treatment for paid time is not established. | Medium — INFERRED | No. | No. | Unit/rounding and payroll treatment. |
| Weekly overtime threshold | `app/weekly/overtime.py::THRESHOLD_SECONDS = 144000`; calculation assumes seconds | Sentinel currently encodes a universal 40-hour threshold for this provisional engine. This is from Sentinel's task/business rule, not evidence of a universal Quartz rule or client eligibility. | High implementation fact; UNKNOWN Quartz scope | Not defensible for production until populations/policy confirmed. | No. | Confirm covered employee groups, workweek definition, exceptions, premium rules, and effective dates. |
| Payroll week and overnight handling | Weekly builder groups by Quartz `shift_date`; `weekly/overtime.py` sums caller-provided eligible seconds | Sunday–Saturday is current Sentinel requirement. No Quartz rule found for allocating overnight sessions, shift_date deviations, breaks, or split weeks. | High grouping implementation; UNKNOWN Quartz policy | Not enough to calculate payroll. | No. | Quartz/payroll policy for shift-date anchoring and week boundary allocation. |
| Source precedence and payroll overrides | `ActivityDataSource` enum and docs list alternative source representations; payable resolver does not select a source | Versions must not be summed. No authoritative rule establishes which version controls payroll or whether session totals supersede activity timelines. | VERIFIED that sources are separate labels; UNKNOWN precedence | No. | No. | Version authority/finality and override rules. |

## Answers to eligibility questions

1. **Activity types/descriptions:** unknown. No enum/catalogue endpoint or dictionary exists in this repository. The connector accepts integer activity type IDs. Do not infer type 7 from the text `OT Break`.
2. **Payable, unpaid, excluded, conditional types:** unknown. No eligibility rules are implemented in the connector or weekly resolver.
3. **Policy dimensions:** unknown; no effective-dated client/site/country/campaign/employee eligibility model found.
4. **Timestamp vs stored duration:** Sentinel's analytical `duration_seconds` is derived from timestamps and truncated to integer seconds; raw Quartz `duration` is retained separately. Neither is established as payroll-authoritative.
5. **Regular/OT metadata authority:** unknown. Both values are passed through without validation of unit or provenance. The sample payload is not proof.
6. **Regular/OT calculation:** Quartz calculation logic is not present. Sentinel's current calculator only applies a provisional threshold to supplied eligible-second totals.
7. **Payroll override:** only `payroll_adjusted` and its timestamp are mapped. No before/after amount or adjustment ledger is available in the documented contract.
8. **40-hour threshold scope:** encoded in Sentinel as 144,000 seconds; universal Quartz scope is unknown.
9. **Overnight/week boundary behavior:** Quartz `shift_date` is authoritative for Sentinel grouping, but payable allocation rules are unknown.

## Read-only requests for Quartz payroll owner

No payroll/type-catalog API is documented in the local contract. Ask a Quartz administrator to identify the supported table and API names first, then run read-only queries with an account limited to `SELECT`.

Discover type and audit-related catalogues (PostgreSQL; names are not assumed):

```sql
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
  AND (table_name ILIKE '%activity%type%'
       OR table_name ILIKE '%payroll%'
       OR table_name ILIKE '%audit%'
       OR table_name ILIKE '%time%rule%')
ORDER BY table_schema, table_name, ordinal_position;
```

Request a sanitized data dictionary and historical effective-date rules for:

- every activity type ID and description;
- payable eligibility/exclusion and conditional criteria;
- `regular_hour`, `overtime`, and `duration` units, precision, rounding, and source authority;
- status/dispute enums and `ready_for_payroll` / payroll-adjusted finality;
- weekly work rule and population eligibility; and
- activity type and payroll policy changes over time.

Request a payroll calculation response for a synthetic or approved sample session that includes input intervals, exclusions, breaks, regular totals, overtime totals, unit definitions, and rounding. Reconcile the response to the same immutable source record IDs. Do not use a live employee's confidential payroll data for this contract check unless authorized.
