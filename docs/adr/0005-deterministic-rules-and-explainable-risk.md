# ADR 0005 - Deterministic rules and explainable risk scoring

## Status
Accepted

## Decision
Sentinel evaluates normalized, immutable employee-day evidence with deterministic rule classes. Each finding records a stable rule ID, category, severity, evidence confidence, risk contribution, reason, and supporting evidence. The aggregate score is a transparent capped sum of rule contributions.

## Rationale
Workforce-integrity findings can affect payroll, employment investigations, and compliance decisions. A black-box score without traceable evidence is not acceptable. Rules must be replayable against the same immutable ingestion run and produce the same result.

## Important distinction
Evidence confidence and rule severity are different concepts. A critical rule can have reduced confidence when source-system evidence is incomplete. Sentinel therefore preserves both instead of pretending they are one number.

## Data-quality mitigation
When the strongest Phone/System captured duration is below the configured three-hour threshold, positive manual-time rules are confidence-reduced. This encodes the operational reality that missing capture can indicate a system or phone failure rather than misconduct.

## Deferred
Correlated-rule suppression, peer baselines, supervisor/manager behavioral profiles, and statistical outlier scoring are intentionally deferred to the behavioral analytics milestone.
