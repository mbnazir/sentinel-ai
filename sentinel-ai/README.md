# Sentinel AI

Enterprise Workforce Integrity & Intelligence Platform.

Sentinel AI ingests workforce/timekeeping data from external systems such as Quartz, normalizes it, reconstructs activity timelines, executes integrity/fraud rules, generates evidence, scores risk, and provides investigation-ready outputs.

## Current milestone

Milestone 1: Project Foundation

Included:

- FastAPI backend scaffold
- PostgreSQL service
- Redis service
- SQLAlchemy 2.x setup
- Alembic setup
- Configuration management
- Structured logging
- Health/readiness/liveness endpoints
- Standard API response envelope
- Initial exception handling
- Test framework
- Docker Compose
- GitHub Actions CI
- Architecture documentation and ADRs

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Swagger:

```text
http://localhost:8000/docs
```

Health:

```text
http://localhost:8000/api/v1/health
```

## Architecture rule

The domain layer must not depend on FastAPI, SQLAlchemy, Redis, Celery, Quartz, or any external framework.

Quartz belongs in the connector layer only.


## Milestone 2: Quartz Connector + Normalized Data Store

This milestone introduces the ingestion boundary. Sentinel now stores normalized workforce sessions and activities in its own database instead of analyzing Quartz directly.

New capabilities:

- Connector synchronization API
- Normalized sessions table
- Normalized activities table
- External source tracking
- Quartz REST client scaffold
- Shift-date range ingestion contract
- Import summary response

Example sync call:

```bash
curl -X POST http://localhost:8000/api/v1/connectors/1/sync   -H "Content-Type: application/json"   -d '{"shift_date_from":"2026-07-01","shift_date_to":"2026-07-05"}'
```


## Milestone 2: Quartz Connector + Normalized Data Store

This milestone introduces the ingestion boundary. Sentinel now stores normalized workforce sessions and activities in its own database instead of analyzing Quartz directly.

New capabilities:

- Connector synchronization API
- Normalized sessions table
- Normalized activities table
- External source tracking
- Quartz REST client scaffold
- Shift-date range ingestion contract
- Import summary response

Example sync call:

```bash
curl -X POST http://localhost:8000/api/v1/connectors/1/sync   -H "Content-Type: application/json"   -d '{"shift_date_from":"2026-07-01","shift_date_to":"2026-07-05"}'
```

## Milestone 3: Timeline Reconstruction Engine

Added:

- Activity-level timeline domain model
- Atomic timeline segment builder
- Source duration comparator
- Timeline mapper
- Timeline API scaffold
- Timeline reconstruction tests
- Timeline documentation and ADR

## Milestone 4: Activity Matching Engine

Added:

- Confidence-based activity matcher
- Match classifications: exact, extended, shortened, shifted, type_changed, inserted, deleted
- Source match service
- Matching API scaffold
- Matcher tests
- Activity matching documentation and ADR

## Milestone 5: Rule Engine

Added:

- Plugin-style deterministic rule framework
- RuleContext, RuleResult, Evidence, Severity
- First activity-level integrity rules
- Session duration increase rule
- Rules API scaffold
- Rule tests
- Rule engine documentation and ADR

## Milestone 6: Risk Scoring Engine

Added:

- RiskLevel model
- RiskAssessment domain model
- Weighted risk scorer
- Duplicate rule dampening
- Combination escalation
- Risk API scaffold
- Risk scoring tests
- Risk scoring documentation and ADR

## Milestone 7: Behavior Analytics Engine

Added:

- BehaviorProfile domain model
- SessionRiskFact model
- Behavior metrics
- Trend detection
- Peer comparison
- Agent and supervisor profile aggregation
- Behavior risk scoring
- Behavior API scaffold
- Tests
- Documentation + ADR

## Milestone 8: Investigation Case Management

Added:

- Investigation case domain model
- Investigation status lifecycle
- Priority mapping from risk score
- Case creation from risk assessments
- Assignment, transition, and comment services
- Investigation API scaffold
- Tests
- Documentation + ADR

## Milestone 9: AI Investigator / Evidence Narrative Engine

Added:

- AI provider abstraction
- Mock AI provider
- OpenAI provider scaffold
- Investigation prompt builder
- Narrative parser
- Investigation narrative service
- AI API scaffold
- AI tests
- Documentation + ADR

## Milestone 10: Persistence-backed Repositories + Workflow APIs

Added:

- Investigation persistence models
- Investigation migration
- InvestigationRepository
- NarrativeRepository
- Workflow service
- Workflow APIs
- API response mapper
- Workflow tests
- Documentation + ADR
