# Phase 2.6 Data Gap Matrix

## Evidence boundary

Repository evidence is directly inspected. The named ingestion run's status/counts below were supplied as verified prior-phase evidence, but could not be independently re-read in this discovery session: a read-only query through Sentinel's configured database connection failed during DNS resolution (`gaierror`). No session-level rows were fetched. The run is not a complete payroll week.

**Labels:** VERIFIED = explicit code/schema/documentation or supplied run fact; INFERRED = plausible from mapping/name but not contractually established; UNKNOWN = no evidence or inaccessible authoritative source. Confidence describes the supporting evidence, not probability of fraud.

| Need / field | Status | Confidence and source | Stored now? | Suitable for payroll? | Suitable for attribution? | Gap / next evidence |
|---|---|---|---|---|---|---|
| Session shift date | VERIFIED | High; connector treats Quartz `shift_date` as authoritative grouping date | Yes, first-class | Grouping only | No | Confirm timezone/week allocation rules. |
| Session start/end | VERIFIED | High; maps `start_date`/`end_date` | Yes | Elapsed context only | No | Confirm payable alignment and overnight policy. |
| `regular_hour`, `overtime` values | VERIFIED as raw persistence; UNKNOWN units and authority | High mapping / Low semantics; connector and integration example conflict with seconds-like reported values | Yes, non-null metadata only | No | No | Quartz unit/precision/finality contract and reconcile to payroll export. |
| Activity type ID and description | VERIFIED ID storage; UNKNOWN type meanings | High ID mapping; no dictionary endpoint/file found | ID yes; description no | No | Classification comparison only | Authoritative type dictionary and effective dates. |
| Payable eligibility by type/status/population | UNKNOWN | No implementation or Quartz contract | No | No | No | Effective-dated policy matrix by client/site/country/campaign/employee. |
| Time calculation and rounding | VERIFIED Sentinel computes integer endpoint difference; UNKNOWN Quartz payroll calculation | Connector uses `int((end-start).total_seconds())`; preserves raw Quartz duration separately | Partial | No | No | Confirm exact precision, break deductions, interval source, rounding. |
| Source-version data_source_id | VERIFIED labels | High; enum/docs/user-supplied semantics | Yes | Do not sum; no precedence contract | Does not identify human | Version finality and source precedence. |
| Activity editor principal | UNKNOWN / absent from current activity contract | High for absence from mapped fields; no actor ID in `NormalizedActivity` | No | No | No | Quartz audit event with authenticated actor and exact activity linkage. |
| Session actor-like metadata (`closed_by`, `resolve_dispute_by`) | VERIFIED raw preservation; UNKNOWN meaning | Connector copies fields as metadata; no semantics in local docs | Yes when non-null | No | Not yet | ID/type dictionary, event scope and principal provenance. |
| Assigned supervisor/manager | VERIFIED assignment fields | High; separate normalized fields | Yes | No | Not editor evidence | Historical assignment only for context. |
| Session workflow action timestamps | VERIFIED timestamps; UNKNOWN action target | High mapping; no event/action IDs | Yes | No | No exact edit attribution | Event-level action IDs and relation to revised interval. |
| Activity `created_at`/`updated_at` | VERIFIED timestamp mapping; UNKNOWN semantics | High mapping; local docs do not define meaning | Yes | No | Not authoritative edit time | Quartz semantics and linkage to actor/event. |
| Before/after edit payload | UNKNOWN / absent from mapped contract | `NormalizedActivity` has no before/after fields; activity comparison derives interval differences from stage rows | No direct event payload | No verified baseline | No verified action | Audit/history API or explicit revision records. |
| Approval/rejection | UNKNOWN semantics | Integer status/dispute columns only | Partial state IDs | No finality inference | No actor inference | State dictionary, transition history, actor/time. |
| Ingestion run a62525d0-3d22-4944-a4f3-5cc1540854f7 | VERIFIED as supplied: failed, 17,600 session snapshots, source reconciliation incomplete, predominantly one shift date; independent DB verification unavailable | Medium; previous-phase user-provided result; configured read query could not connect | Reported yes | Not a week | No | Read-only aggregate verification when DB returns; inspect error and date distribution. |
| Run completeness/reconciliation | VERIFIED gap | High; `IngestionRunModel` stores status/date range/counters, but no Quartz expected counts/per-date success manifest | Partial counters only | No | No | Quartz expected session/activity counts per date and successful-empty markers. |
| Activity comparison | VERIFIED observation capability | High; pairwise, run-scoped UTC interval comparator; WF-005 provisional | Yes, computed read-only | Reclassification seconds are not payable seconds | No editor identification | Maintain provisional classification until audit and payroll contracts arrive. |
| Weekly 40-hour overtime threshold | VERIFIED as Sentinel implementation/business assumption; UNKNOWN Quartz population scope | High code fact (`144000` constant); no Quartz validation | Calculator exists, output gated provisional | Not production-defensible universally | No | Payroll owner confirms applicable groups, policies, exceptions and effective dates. |
| Tenant/employee authorization | VERIFIED gap | High; JWT `Principal` has subject+role only; no tenant or employee membership map | No fine-grained grant | n/a | n/a | Trusted tenant/user/employee access relationship and policy enforcement. |
| Payroll evidence read audit | VERIFIED gap | High; request correlation middleware exists, but no read-access event for employee payroll evidence | Correlation ID only | n/a | n/a | Immutable access audit event with requester, resource, purpose, allow/deny, correlation and time. |

## Failed run handling notes

The ingestion service commits batches and updates counters, then marks the run failed if a later operation raises. Thus partial snapshots can remain under a failed run; a failed run is not evidence of source completeness. Existing session/activity unique constraints prevent duplicate source IDs inside a run, but there is no resumable per-date/page checkpoint in the current contract. Do not combine the failed run with another run or infer a full payroll week from its snapshot count.

## Read-only verification when Sentinel DB is available

For the named run, retrieve only run metadata and aggregate counts/date/source distributions:

```sql
SELECT id, status, shift_date_from, shift_date_to, session_count, activity_count,
       started_at, completed_at, error_message
FROM ingestion_runs
WHERE id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7';

SELECT count(*) AS snapshot_sessions, min(shift_date) AS first_shift_date,
       max(shift_date) AS last_shift_date, count(DISTINCT shift_date) AS dates_seen
FROM session_snapshots
WHERE ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7';

SELECT shift_date, count(*) AS sessions
FROM session_snapshots
WHERE ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7'
GROUP BY shift_date ORDER BY shift_date;

SELECT data_source_id, count(*) AS activities
FROM activity_snapshots
WHERE ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7'
GROUP BY data_source_id ORDER BY data_source_id;
```

Do not return raw employee payroll rows for this aggregate readiness check. Compare counts to Quartz expected counts; Sentinel counters alone cannot reconcile source completeness.
