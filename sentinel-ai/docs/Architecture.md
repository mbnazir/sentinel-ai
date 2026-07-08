# Sentinel AI Architecture

Sentinel AI follows Clean Architecture and Domain-Driven Design.

## High-level flow

```text
External Workforce System
        |
        v
Connector
        |
        v
Normalization Pipeline
        |
        v
Sentinel Operational Store
        |
        v
Timeline Engine
        |
        v
Rule Engine
        |
        v
Risk Scoring
        |
        v
Investigations / Dashboard / AI Summaries
```

Quartz is a connector only. The core engine does not know Quartz tables, columns, or workflow-specific internals.


## Normalized workforce store

Milestone 2 introduced normalized tables:

- `normalized_login_sessions`
- `normalized_activities`
- `external_sources`

These tables isolate analytics from source-system schemas and make every scan reproducible.
