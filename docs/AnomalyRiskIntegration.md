# Milestone 25 — Anomaly Risk Integration

## Purpose

Milestone 24 added anomaly scoring, but a separate anomaly score is not enough. Milestone 25 wires anomaly findings into Sentinel's risk model.

## Added

- `AnomalyRuleAdapter`
- `AnomalyRiskService`
- `BehaviorAnomalyPipeline`
- Integration tests

## Design

Behavioral anomalies are converted into normal `RuleResult` objects.

That means the existing risk scorer remains the single aggregation path for:

- deterministic activity rules
- session duration rules
- behavior anomaly rules

## Why this matters

Investigators should not see disconnected scores. A session, agent, supervisor, or payroll operator should have one risk assessment with explainable evidence.

## Next step

Persist anomaly scores and attach anomaly evidence to investigation cases automatically.
