# Behavior Intelligence Engine

This milestone replaces behavior analytics scaffolding with a persistent behavior intelligence layer.

## Added

- behavior feature snapshot persistence
- peer deviation persistence
- behavior repository
- behavior intelligence orchestration service
- session fact builder
- persistent behavior profile API

## Database tables

- `behavior_feature_snapshots`
- `behavior_peer_deviations`

## API

```text
GET /api/v1/behavior-intelligence/profiles/{entity_type}?organization_id=ORG1
```

Supported entity types initially:

- `agent`
- `supervisor`

## Design

The behavior intelligence service produces rolling profiles from session facts, persists the resulting feature snapshots, and calculates peer deviations for explainable outlier detection.

## What is intentionally not included yet

- scheduled refresh jobs
- persisted scan-result to behavior-fact ETL
- manager/payroll/campaign/site profiles
- ML anomaly detection
