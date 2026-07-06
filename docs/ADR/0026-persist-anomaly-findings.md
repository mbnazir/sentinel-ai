# ADR-0026: Persist anomaly findings

## Status

Accepted

## Context

Anomaly results must be auditable, trendable, and available to dashboards.

## Decision

Persist anomaly findings separately from behavior snapshots and rule results.

## Consequences

- Dashboards can list active anomaly findings.
- Investigations can attach anomaly evidence.
- Future ML models can write to the same finding table.
