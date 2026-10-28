# Milestone 3 - Timeline Reconstruction and Activity Matching

## Objective
Turn immutable Quartz snapshots into a canonical employee-day timeline and emit deterministic, source-aware evidence suitable for the Sentinel rule engine.

## Delivered
- Canonical `EmployeeDayTimeline` keyed by ingestion run, agent and shift date.
- Preservation of every login session on that employee-day.
- Activity grouping for Phone, System, Agent, Supervisor, Manager and Payroll.
- Chain-aware activity matching with confidence scores.
- Detection of inserted, removed, extended, shortened, shifted, type-changed and compound activity changes.
- Detection of intra-source activity gaps and overlaps.
- Detection of overlapping login sessions for the same employee-day.
- Neutral evidence objects containing source lineage, before/after IDs, seconds changed and confidence.
- Timeline and timeline-analysis REST endpoints.

## API
`GET /api/v1/timelines/{agent_id}/{shift_date}?ingestion_run_id=<uuid>`

Returns the reconstructed canonical employee-day timeline.

`GET /api/v1/timelines/{agent_id}/{shift_date}/analysis?ingestion_run_id=<uuid>`

Returns timeline comparisons and structured evidence.

## Non-goals
Milestone 3 does not classify a person as fraudulent, calculate a fraud score, infer intent, or perform behavioral outlier analysis. Those responsibilities belong to deterministic rules and behavioral analytics in later milestones.
