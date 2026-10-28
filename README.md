# Sentinel AI v0.13.0

Milestone 13 adds the evidence-grounded AI Investigator plus complete local Quartz deployment/UAT tooling.

# Sentinel AI v0.12.0 Release Candidate

Milestone 12 adds enterprise security controls, production deployment topology and Quartz integration hardening.

# Sentinel AI v0.11.0

Milestone 11 adds the React investigator dashboard and case workspace.

# Sentinel AI v0.10.0

Milestone 10 adds scan finalization and production reliability controls.

# Sentinel AI v0.9.0

Milestone 9 adds durable chunk execution and the full deterministic scan pipeline.

# Sentinel AI v0.8.0

Milestone 8 adds distributed scan execution and worker orchestration.

# Sentinel AI v0.7.0

Milestone 7 adds durable scans, immutable findings, investigation case workflow and audit history.

# Sentinel AI v0.6.0

Milestone 6 adds organizational behavioral intelligence and relationship-level collusion risk signals.

# Sentinel AI v0.5.0

Milestone 5 adds behavioral analytics and cross-shift pattern detection.

# Sentinel AI

Enterprise Workforce Integrity & Intelligence Platform.

## Milestone 1.2

This repository is the production-oriented Python foundation. It intentionally contains no fraud rules yet.

### Start locally

1. Copy `.env.example` to `.env`.
2. Replace `JWT_SECRET` before any shared environment use.
3. Run `docker compose up --build`.
4. Open Swagger at `http://localhost:8000/docs`.

### Platform endpoints

- `GET /live`
- `GET /ready`
- `GET /api/v1/health`
- `GET /api/v1/connectors`
- `POST /api/v1/connectors`

### Architecture rule

Quartz is read-only and accessed through a connector. Sentinel analytics consume normalized records, never Quartz ORM/database models directly.

### Analytical grain

Sentinel's primary analytical context is `agent + shift_date`, with all login sessions and activities for that employee-day retained. Session-level evidence remains available underneath that context.

## Milestone 2 - Quartz Connector and Snapshot Ledger

Implemented capabilities:

- Quartz REST connector with cursor pagination and bounded extraction batches.
- Inclusive shift-date range ingestion rather than single-session extraction.
- Immutable ingestion runs, session snapshots, and activity snapshots.
- SHA-256 canonical hashes for snapshot integrity and comparison.
- Strict Quartz activity source mapping: Phone (0), System (1), Agent (2), Supervisor (3), Manager (4), Payroll (5).
- Preserves multiple login sessions for the same `agent_id + shift_date`.
- Employee-day endpoint groups all sessions for an agent/shift date and summarizes activities by source.
- Connector credentials are not persisted in Sentinel connector metadata.

See `docs/quartz-api-contract.md` and ADR 0003 before implementing the Quartz-side endpoints.

## Milestone 3 - Timeline Reconstruction

Sentinel now reconstructs canonical employee-day timelines from immutable snapshot data and compares activity versions across the Phone -> System -> Agent -> Supervisor -> Manager -> Payroll workflow. The matcher emits neutral evidence such as inserted/removed activities, extensions, type changes, gaps, overlaps and overlapping login sessions. Fraud classification is intentionally deferred to the rule engine.

Timeline endpoints:

- `GET /api/v1/timelines/{agent_id}/{shift_date}?ingestion_run_id=<uuid>`
- `GET /api/v1/timelines/{agent_id}/{shift_date}/analysis?ingestion_run_id=<uuid>`

## Milestone 4 - Deterministic Integrity Rules

Sentinel now evaluates timeline evidence with 24 deterministic integrity/workflow/payroll/data-quality rules. Findings preserve stable rule IDs, evidence confidence, severity, risk contribution, reason, and evidence. The engine deliberately reports risk rather than asserting fraud.

Assessment endpoint:

- `GET /api/v1/assessments/{agent_id}/{shift_date}?ingestion_run_id=<uuid>`

Important: a Phone/System captured duration below three hours reduces confidence for positive manual-time findings and emits a data-quality mitigation note. See ADR 0005 and `docs/milestones/M4-deterministic-rule-engine.md`.
