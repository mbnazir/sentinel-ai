-- Sentinel AI Fraud Detection | Read-only audit | 2026-08-26 observation
-- Run with psql -v ON_ERROR_STOP=1 -f sentinel_data_quality_audit.sql
BEGIN TRANSACTION READ ONLY;
SET LOCAL statement_timeout = '120s';
\echo '=== 1. Ingestion run and stored totals ==='
SELECT r.id, r.status, r.shift_date_from, r.shift_date_to, r.started_at, r.completed_at,
       r.session_count AS recorded_sessions, r.activity_count AS recorded_activities,
       (SELECT count(*) FROM session_snapshots s WHERE s.ingestion_run_id = r.id) AS actual_sessions,
       (SELECT count(*) FROM activity_snapshots a WHERE a.ingestion_run_id = r.id) AS actual_activities
FROM ingestion_runs r WHERE r.id = '026961c1-9442-4818-af5f-620c0be3d62f';

\echo '=== 2. Session quality ==='
SELECT count(*) AS total_sessions,
 count(*) FILTER (WHERE btrim(source_session_id) = '') AS blank_session_ids,
 count(*) FILTER (WHERE btrim(agent_id) = '') AS blank_agent_ids,
 count(*) FILTER (WHERE end_at IS NULL) AS open_ended_sessions,
 count(*) FILTER (WHERE end_at < start_at) AS reversed_intervals,
 count(*) FILTER (WHERE end_at = start_at) AS zero_length_intervals,
 count(*) FILTER (WHERE end_at > start_at AND end_at - start_at > interval '24 hours') AS over_24h_intervals,
 count(*) FILTER (WHERE shift_date <> DATE '2026-08-26') AS outside_requested_shift_date,
 count(*) FILTER (WHERE content_hash !~ '^[0-9a-fA-F]{64}$') AS invalid_hash_format,
 count(*) FILTER (WHERE multiple_logins < 0) AS negative_multiple_logins,
 count(*) FILTER (WHERE payroll_adjusted AND payroll_adjusted_at IS NULL) AS adjusted_without_timestamp
FROM session_snapshots WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f';

\echo '=== 3. Activity quality ==='
SELECT count(*) AS total_activities,
 count(*) FILTER (WHERE btrim(source_activity_id) = '') AS blank_activity_ids,
 count(*) FILTER (WHERE btrim(source_session_id) = '') AS blank_session_ids,
 count(*) FILTER (WHERE agent_id IS NULL OR btrim(agent_id) = '') AS missing_agent_ids,
 count(*) FILTER (WHERE end_at IS NULL) AS open_ended_activities,
 count(*) FILTER (WHERE end_at < start_at) AS reversed_intervals,
 count(*) FILTER (WHERE end_at = start_at) AS zero_length_intervals,
 count(*) FILTER (WHERE duration_seconds < 0) AS negative_durations,
 count(*) FILTER (WHERE duration_seconds = 0) AS zero_durations,
 count(*) FILTER (WHERE duration_seconds > 86400) AS over_24h_durations,
 count(*) FILTER (WHERE inactivity_seconds < 0) AS negative_inactivity,
 count(*) FILTER (WHERE end_at IS NOT NULL AND duration_seconds IS NOT NULL AND abs(extract(epoch FROM (end_at - start_at)) - duration_seconds) > 60) AS duration_interval_discrepancy_over_60s,
 count(*) FILTER (WHERE content_hash !~ '^[0-9a-fA-F]{64}$') AS invalid_hash_format
FROM activity_snapshots WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f';

\echo '=== 4. Orphan activities and mismatched agents ==='
SELECT count(*) FILTER (WHERE s.id IS NULL) AS orphan_activities,
 count(*) FILTER (WHERE s.id IS NOT NULL AND a.agent_id IS NOT NULL AND a.agent_id <> s.agent_id) AS agent_mismatches,
 count(DISTINCT a.source_session_id) FILTER (WHERE s.id IS NULL) AS distinct_orphan_source_sessions
FROM activity_snapshots a LEFT JOIN session_snapshots s
 ON s.ingestion_run_id = a.ingestion_run_id AND s.source_system = a.source_system AND s.source_session_id = a.source_session_id
WHERE a.ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f';

\echo '=== 5. Activity distribution by data source ==='
SELECT data_source_id, count(*) AS activities, count(DISTINCT source_session_id) AS distinct_sessions,
 count(*) FILTER (WHERE duration_seconds < 0) AS negative_durations
FROM activity_snapshots WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f'
GROUP BY data_source_id ORDER BY activities DESC;

\echo '=== 6. Activity distribution by type ==='
SELECT activity_type_id, count(*) AS activities, count(DISTINCT source_session_id) AS distinct_sessions
FROM activity_snapshots WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f'
GROUP BY activity_type_id ORDER BY activities DESC;

\echo '=== 7. Session distribution and action metadata ==='
SELECT count(DISTINCT agent_id) AS distinct_agents,
 count(DISTINCT site_id) AS distinct_sites,
 count(*) FILTER (WHERE dispute_reason_id IS NOT NULL) AS sessions_with_dispute_reason,
 count(*) FILTER (WHERE agent_action_at IS NOT NULL) AS sessions_with_agent_action,
 count(*) FILTER (WHERE supervisor_action_at IS NOT NULL) AS sessions_with_supervisor_action,
 count(*) FILTER (WHERE manager_action_at IS NOT NULL) AS sessions_with_manager_action,
 count(*) FILTER (WHERE payroll_adjusted) AS payroll_adjusted_sessions,
 count(*) FILTER (WHERE ready_for_payroll) AS payroll_ready_sessions
FROM session_snapshots WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f';

\echo '=== 8. Historical observation comparison: shared session hashes ==='
SELECT count(*) AS shared_sessions,
 count(*) FILTER (WHERE old.content_hash = new.content_hash) AS unchanged_hashes,
 count(*) FILTER (WHERE old.content_hash <> new.content_hash) AS changed_hashes
FROM session_snapshots old JOIN session_snapshots new
 ON old.source_system = new.source_system AND old.source_session_id = new.source_session_id
WHERE old.ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7'
  AND new.ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f';

COMMIT;
