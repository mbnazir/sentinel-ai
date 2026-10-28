\set ON_ERROR_STOP on
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;

-- QF-001: compare two immutable observation runs; no writes.
-- Status 4 = Accepted by Manager; status 5 = Rejected by Manager.
-- Payroll readiness is NOT proof of payroll finalization.
WITH earlier AS (
    SELECT * FROM public.session_snapshots
    WHERE ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7'::uuid
),
later AS (
    SELECT * FROM public.session_snapshots
    WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f'::uuid
),
findings AS (
    SELECT
        e.source_system,
        e.source_session_id,
        e.agent_id,
        e.supervisor_status_id AS earlier_status_id,
        l.supervisor_status_id AS later_status_id,
        CASE WHEN e.supervisor_status_id = 4 THEN 'Accepted by Manager -> Rejected by Manager'
             ELSE 'Rejected by Manager -> Accepted by Manager' END AS transition,
        e.ready_for_payroll AS earlier_payroll_ready,
        l.ready_for_payroll AS later_payroll_ready,
        e.manager_action_at AS earlier_manager_action_at,
        l.manager_action_at AS later_manager_action_at,
        e.observed_at AS earlier_observed_at,
        l.observed_at AS later_observed_at,
        e.content_hash AS earlier_content_hash,
        l.content_hash AS later_content_hash,
        e.ingestion_run_id AS earlier_ingestion_run_id,
        l.ingestion_run_id AS later_ingestion_run_id,
        'QF-001'::text AS rule_id,
        'MEDIUM'::text AS initial_severity,
        'REVIEW_REQUIRED'::text AS disposition
    FROM earlier e
    JOIN later l
      ON l.source_system = e.source_system
     AND l.source_session_id = e.source_session_id
    WHERE e.supervisor_status_id IN (4, 5)
      AND l.supervisor_status_id IN (4, 5)
      AND e.supervisor_status_id <> l.supervisor_status_id
      AND e.ready_for_payroll IS TRUE
      AND l.ready_for_payroll IS TRUE
)
SELECT * FROM findings ORDER BY source_session_id;

-- Aggregate counts for reproducible rule validation.
WITH earlier AS (
    SELECT source_system, source_session_id, supervisor_status_id, ready_for_payroll
    FROM public.session_snapshots
    WHERE ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7'::uuid
),
later AS (
    SELECT source_system, source_session_id, supervisor_status_id, ready_for_payroll
    FROM public.session_snapshots
    WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f'::uuid
)
SELECT
    'QF-001' AS rule_id,
    COUNT(*) FILTER (WHERE e.supervisor_status_id = 4 AND l.supervisor_status_id = 5) AS accepted_to_rejected,
    COUNT(*) FILTER (WHERE e.supervisor_status_id = 5 AND l.supervisor_status_id = 4) AS rejected_to_accepted,
    COUNT(*) AS total_findings
FROM earlier e JOIN later l
  ON e.source_system = l.source_system
 AND e.source_session_id = l.source_session_id
WHERE e.ready_for_payroll IS TRUE
  AND l.ready_for_payroll IS TRUE
  AND ((e.supervisor_status_id = 4 AND l.supervisor_status_id = 5)
    OR (e.supervisor_status_id = 5 AND l.supervisor_status_id = 4));

COMMIT;
