# ADR-0025: Treat anomaly scores as rule evidence

## Status

Accepted

## Context

Sentinel already has a rule evidence model and risk scorer. Introducing a separate anomaly score path would fragment investigation evidence.

## Decision

Convert anomaly scores into `RuleResult` objects.

## Consequences

- Risk scoring stays unified.
- Anomaly evidence becomes case evidence.
- AI narratives can summarize anomaly findings the same way as deterministic rule findings.
