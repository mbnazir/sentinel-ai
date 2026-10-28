# Milestone 5 - Behavioral Analytics and Cross-Shift Pattern Detection

Implemented analytical windows over multiple shift dates, agent peer comparison, recurrence detection, rounded-addition patterns, weekday concentration, supervisor-agent concentration, and pair-pattern findings.

Important limitation: the current Quartz snapshot contains supervisor_id but not an explicit manager_id hierarchy. Manager-level peer/collusion analytics must wait for a trustworthy manager relationship field/API; Sentinel will not infer it. Campaign baselines can be built from primary_campaign_id retained in session snapshots.

Behavioral analytics are intentionally separate from deterministic risk assessments.
