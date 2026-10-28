BEGIN TRANSACTION READ ONLY;

WITH historical AS (
    SELECT *
    FROM session_snapshots
    WHERE ingestion_run_id = 'a62525d0-3d22-4944-a4f3-5cc1540854f7'
),
current_observation AS (
    SELECT *
    FROM session_snapshots
    WHERE ingestion_run_id = '026961c1-9442-4818-af5f-620c0be3d62f'
)
SELECT
    COUNT(*) AS shared_sessions,

    COUNT(*) FILTER (
        WHERE h.content_hash IS DISTINCT FROM c.content_hash
    ) AS changed_hashes,

    COUNT(*) FILTER (
        WHERE h.status_id IS DISTINCT FROM c.status_id
    ) AS status_changes,

    COUNT(*) FILTER (
        WHERE h.dispute_state IS DISTINCT FROM c.dispute_state
    ) AS dispute_state_changes,

    COUNT(*) FILTER (
        WHERE h.supervisor_status_id IS DISTINCT FROM c.supervisor_status_id
    ) AS supervisor_status_changes,

    COUNT(*) FILTER (
        WHERE h.ready_for_payroll IS DISTINCT FROM c.ready_for_payroll
    ) AS payroll_readiness_changes,

    COUNT(*) FILTER (
        WHERE h.payroll        WHERE h.payroll        WHERE h.payred        WHERE h.l_adjustment_changes,

    COUNT(*)    COUNT(        WHERE h.agent_action_at IS DISTINCT FROM c.agent_action_at
    ) AS agent_action_changes,

    COUNT(*) FILTER (
        WHERE h.su        WHERE h.su       TINCT FROM c.supervisor_action_at
    ) AS supervisor_action_changes,

    COUNT(*) FILTER (
        WHERE h.mana        WHERE h.manaTINCT FROM c.manager_action_at
    ) AS manager_action_changes
    ) AS manager_acJOIN current_observation c
                                                       ss                      ion_id;

COMMIT;
